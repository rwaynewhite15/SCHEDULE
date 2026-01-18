import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, ttk
from tkcalendar import Calendar
import anthropic
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import requests

# Load environment variables from .env file
load_dotenv()

# Color scheme for categories - New categories: Spiritual, Physical, Emotional, Intellectual
CATEGORY_COLORS = {
    "Spiritual": {"bg": "#9B59B6", "fg": "white"},      # Purple
    "Physical": {"bg": "#E74C3C", "fg": "white"},       # Red
    "Emotional": {"bg": "#F39C12", "fg": "white"},      # Orange
    "Intellectual": {"bg": "#3498DB", "fg": "white"}    # Blue
}

class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Scheduler with Weather Forecast")
        self.root.geometry("1600x900")
        
        # Modern theme colors
        self.bg_color = "#f5f5f5"
        self.accent_color = "#2c3e50"
        self.button_color = "#3498db"
        self.hover_color = "#2980b9"
        
        self.root.configure(bg=self.bg_color)
        
        self.data_file = "calendar_data.json"
        self.weather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.weather_location = os.getenv("WEATHER_LOCATION", "Martinsville,IN,US")
        
        self.schedule = self.load_course_schedule()
        self.listbox_index_to_event = {}  # NEW: Map listbox indices to events
        self.create_widgets()
        
        # Save on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def parse_time_for_sorting(self, time_str):
        """Convert time string to minutes from midnight for sorting"""
        if not time_str:
            return 9999  # Put events without time at the end
        
        time_str = time_str.strip().upper()
        
        try:
            # Handle 12-hour format (e.g., "2:30 PM", "10:00 AM")
            if 'AM' in time_str or 'PM' in time_str:
                time_part = time_str.replace('AM', '').replace('PM', '').strip()
                is_pm = 'PM' in time_str
                
                if ':' in time_part:
                    hours, minutes = map(int, time_part.split(':'))
                else:
                    hours = int(time_part)
                    minutes = 0
                
                # Convert to 24-hour format
                if is_pm and hours != 12:
                    hours += 12
                elif not is_pm and hours == 12:
                    hours = 0
                    
                return hours * 60 + minutes
            
            # Handle 24-hour format (e.g., "14:30", "09:00")
            elif ':' in time_str:
                hours, minutes = map(int, time_str.split(':'))
                return hours * 60 + minutes
            
            # Handle single hour without minutes (e.g., "9", "17")
            else:
                hours = int(time_str)
                return hours * 60
        
        except ValueError:
            return 9999  # Invalid time format, put at the end

    def get_category(self, event_text):
        """Determine category based on event text"""
        text_lower = event_text.lower()
        # Map old categories to new ones for compatibility
        if "spiritual" in text_lower or "meditation" in text_lower or "prayer" in text_lower:
            return "Spiritual"
        elif "physical" in text_lower or "exercise" in text_lower or "gym" in text_lower:
            return "Physical"
        elif "emotional" in text_lower or "therapy" in text_lower or "support" in text_lower:
            return "Emotional"
        elif "intellectual" in text_lower or "learning" in text_lower or "study" in text_lower:
            return "Intellectual"
        # Default to Intellectual for assignments/quizzes
        return "Intellectual"

    def get_weather_for_date(self, date_str):
        """Fetch weather forecast for a specific date"""
        if not self.weather_api_key:
            return "Weather API key not configured.\nAdd OPENWEATHER_API_KEY to .env file."
        
        try:
            # Parse and compare dates using date-only
            date_obj = datetime.strptime(date_str, "%m/%d/%y").date()
            today = datetime.now().date()
            
            # Calculate days from today
            days_diff = (date_obj - today).days
            
            # If the date is today, get current weather
            if days_diff == 0:
                url = f"https://api.openweathermap.org/data/2.5/weather?q={self.weather_location}&appid={self.weather_api_key}&units=imperial"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    temp = data['main']['temp']
                    description = data['weather'][0]['description']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    wind_speed = data['wind']['speed']
                    
                    weather_text = f"📍 {self.weather_location}\n"
                    weather_text += f"📅 {date_obj.strftime('%B %d, %Y')} (Today)\n\n"
                    weather_text += f"🌡️ {temp:.0f}°F (feels like {feels_like:.0f}°F)\n"
                    weather_text += f"☁️ {description.capitalize()}\n"
                    weather_text += f"💧 Humidity: {humidity}%\n"
                    weather_text += f"💨 Wind: {wind_speed:.1f} mph"
                    
                    return weather_text
                else:
                    return f"Could not fetch weather\n(Error: {response.status_code})"
            
            # For future dates (up to 5 days), use forecast API
            elif 0 < days_diff <= 5:
                url = f"https://api.openweathermap.org/data/2.5/forecast?q={self.weather_location}&appid={self.weather_api_key}&units=imperial"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Find forecasts for the target date
                    target_date_str = date_obj.strftime("%Y-%m-%d")
                    matching_forecasts = [
                        f for f in data['list'] 
                        if f['dt_txt'].startswith(target_date_str)
                    ]
                    
                    if matching_forecasts:
                        # Use the midday forecast (around noon) if available
                        midday_forecast = None
                        for f in matching_forecasts:
                            hour = int(f['dt_txt'].split()[1].split(':')[0])
                            if 11 <= hour <= 14:  # Between 11 AM and 2 PM
                                midday_forecast = f
                                break
                        
                        # If no midday forecast, use the first one
                        forecast = midday_forecast or matching_forecasts[0]
                        
                        temp = forecast['main']['temp']
                        feels_like = forecast['main']['feels_like']
                        description = forecast['weather'][0]['description']
                        humidity = forecast['main']['humidity']
                        wind_speed = forecast['wind']['speed']
                        
                        # Get high/low for the day
                        temps = [f['main']['temp'] for f in matching_forecasts]
                        temp_max = max(temps)
                        temp_min = min(temps)
                        
                        weather_text = f"📍 {self.weather_location}\n"
                        weather_text += f"📅 {date_obj.strftime('%B %d, %Y')}\n"
                        weather_text += f"({days_diff} day{'s' if days_diff > 1 else ''} from now)\n\n"
                        weather_text += f"🌡️ High: {temp_max:.0f}°F / Low: {temp_min:.0f}°F\n"
                        weather_text += f"   Around noon: {temp:.0f}°F (feels like {feels_like:.0f}°F)\n"
                        weather_text += f"☁️ {description.capitalize()}\n"
                        weather_text += f"💧 Humidity: {humidity}%\n"
                        weather_text += f"💨 Wind: {wind_speed:.1f} mph"
                        
                        return weather_text
                    else:
                        return f"No forecast available for\n{date_obj.strftime('%B %d, %Y')}"
                else:
                    return f"Could not fetch forecast\n(Error: {response.status_code})"
            
            # For past dates or dates beyond 5 days
            elif days_diff < 0:
                return f"📅 {date_obj.strftime('%B %d, %Y')}\n\n⏮️ This date has passed.\nWeather data not available for past dates."
            else:
                return f"📅 {date_obj.strftime('%B %d, %Y')}\n\n🔮 Forecast only available\nfor the next 5 days.\n\n(This date is {days_diff} days away)"
                
        except requests.exceptions.RequestException as e:
            return f"Network error:\n{str(e)}"
        except Exception as e:
            return f"Error:\n{str(e)}"

    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=self.accent_color)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        title = tk.Label(
            header, 
            text="📅 Life Wellness Calendar", 
            font=("Segoe UI", 20, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        title.pack(pady=15)

        # Main content frame
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Left side - Calendar and Weather
        left_frame = tk.Frame(content_frame, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        cal_label = tk.Label(
            left_frame,
            text="Select Date",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg=self.accent_color
        )
        cal_label.pack(pady=(10, 5))

        # Get today's date for correct calendar display (date-only)
        today = datetime.now().date()

        self.calendar = Calendar(
            left_frame,
            selectmode='day',
            year=today.year,
            month=today.month,
            day=today.day,
            font=("Segoe UI", 16, "bold"),
            headersforeground="white",
            weekendforeground="#e74c3c",
            width=28,
            height=28
        )
        self.calendar.pack(pady=10, padx=10)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

        # Ensure the initial selection is today
        self.calendar.selection_set(today)

        # Weather frame
        weather_label = tk.Label(
            left_frame,
            text="Weather Forecast",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=self.accent_color
        )
        weather_label.pack(pady=(15, 5), padx=10, anchor="w")

        self.weather_display = tk.Label(
            left_frame,
            text="Select a date to see weather",
            font=("Segoe UI", 9),
            bg="#f0f8ff",
            fg="#333",
            justify=tk.LEFT,
            wraplength=250,
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        self.weather_display.pack(padx=10, pady=(0, 10), fill=tk.BOTH)

        # Right side - Events
        right_frame = tk.Frame(content_frame, bg="white")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        events_label = tk.Label(
            right_frame,
            text="Events for Selected Date",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg=self.accent_color
        )
        events_label.pack(pady=(10, 5), padx=10, anchor="w")

        # Event listbox with frame
        listbox_frame = tk.Frame(right_frame, bg="white")
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.event_listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 11),
            height=20,
            bg="white",
            fg="#333",
            selectmode=tk.SINGLE,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        self.event_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.event_listbox.yview)

        # Button frame
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        button_style = {
            "font": ("Segoe UI", 10, "bold"),
            "bg": self.button_color,
            "fg": "white",
            "activebackground": self.hover_color,
            "activeforeground": "white",
            "relief": tk.FLAT,
            "padx": 15,
            "pady": 8,
            "cursor": "hand2"
        }

        add_btn = tk.Button(btn_frame, text="➕ Add Event", command=self.add_item, **button_style)
        add_btn.grid(row=0, column=0, padx=5)

        edit_btn = tk.Button(btn_frame, text="✏️ Edit Event", command=self.edit_item, **button_style)
        edit_btn.grid(row=0, column=1, padx=5)

        del_btn = tk.Button(btn_frame, text="🗑️ Delete Event", command=self.delete_item, **button_style)
        del_btn.grid(row=0, column=2, padx=5)

        ai_btn = tk.Button(
            btn_frame, 
            text="🤖 AI Chatbot", 
            command=self.open_ai_chat,
            font=("Segoe UI", 10, "bold"),
            bg="#9b59b6",
            fg="white",
            activebackground="#8e44ad",
            activeforeground="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        ai_btn.grid(row=0, column=3, padx=5)

        self.refresh_event_listbox()
        self.on_date_select()  # Load weather for initial date

    def add_item(self):
        date = self.calendar.get_date()
        
        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Event")
        dialog.geometry("400x380")
        dialog.configure(bg="white")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Add New Event",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=self.accent_color
        ).pack(pady=(15, 10))

        tk.Label(dialog, text=f"Date: {date}", font=("Segoe UI", 10), bg="white").pack()

        tk.Label(dialog, text="Event Name:", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        event_entry = tk.Entry(dialog, font=("Segoe UI", 10), width=40)
        event_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="Start Time (optional, e.g., 2:30 PM):", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        start_time_entry = tk.Entry(dialog, font=("Segoe UI", 10), width=40)
        start_time_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="End Time (optional, e.g., 4:00 PM):", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        end_time_entry = tk.Entry(dialog, font=("Segoe UI", 10), width=40)
        end_time_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="Category:", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        category_var = tk.StringVar(value="Intellectual")
        category_combo = ttk.Combobox(
            dialog,
            textvariable=category_var,
            values=list(CATEGORY_COLORS.keys()),
            state="readonly",
            font=("Segoe UI", 10)
        )
        category_combo.pack(padx=20, pady=5, fill=tk.X)

        def save_event():
            event_name = event_entry.get().strip()
            start_time = start_time_entry.get().strip()
            end_time = end_time_entry.get().strip()
            category = category_var.get()
            
            if not event_name:
                messagebox.showwarning("Input Error", "Please enter an event name.")
                return
            
            self.schedule.append({
                "date": date,
                "event": event_name,
                "start_time": start_time,
                "end_time": end_time,
                "category": category
            })
            self.refresh_event_listbox()
            self.save_schedule()
            dialog.destroy()

        tk.Button(
            dialog,
            text="Save Event",
            font=("Segoe UI", 10, "bold"),
            bg=self.button_color,
            fg="white",
            command=save_event,
            padx=20,
            pady=8
        ).pack(pady=15)

    def edit_item(self):
        selected = self.event_listbox.curselection()
        if not selected:
            messagebox.showwarning("Edit Event", "No event selected.")
            return
        idx = selected[0]
        # NEW: Use mapping instead of filtered_events()
        if idx not in self.listbox_index_to_event:
            messagebox.showwarning("Edit Event", "Please select an event to edit.")
            return
        event = self.listbox_index_to_event[idx]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Event")
        dialog.geometry("400x380")
        dialog.configure(bg="white")
        dialog.resizable(False, False)
        
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Edit Event",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=self.accent_color
        ).pack(pady=(15, 10))

        tk.Label(dialog, text="Event Name:", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        event_entry = tk.Entry(dialog, font=("Segoe UI", 10), width=40)
        event_entry.insert(0, event.get("event", ""))
        event_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="Start Time (optional):", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        start_time_entry = tk.Entry(dialog, font=("Segoe UI", 10), width=40)
        start_time_entry.insert(0, event.get("start_time", ""))
        start_time_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="End Time (optional):", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        end_time_entry = tk.Entry(dialog, font=("Segoe UI", 10), width=40)
        end_time_entry.insert(0, event.get("end_time", ""))
        end_time_entry.pack(padx=20, pady=5)

        tk.Label(dialog, text="Category:", font=("Segoe UI", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 0))
        category_var = tk.StringVar(value=event.get("category", "Intellectual"))
        category_combo = ttk.Combobox(
            dialog,
            textvariable=category_var,
            values=list(CATEGORY_COLORS.keys()),
            state="readonly",
            font=("Segoe UI", 10)
        )
        category_combo.pack(padx=20, pady=5, fill=tk.X)

        def save_event():
            event_name = event_entry.get().strip()
            start_time = start_time_entry.get().strip()
            end_time = end_time_entry.get().strip()
            category = category_var.get()
            
            if not event_name:
                messagebox.showwarning("Input Error", "Please enter an event name.")
                return
            
            event["event"] = event_name
            event["start_time"] = start_time
            event["end_time"] = end_time
            event["category"] = category
            self.refresh_event_listbox()
            self.save_schedule()
            dialog.destroy()

        tk.Button(
            dialog,
            text="Update Event",
            font=("Segoe UI", 10, "bold"),
            bg=self.button_color,
            fg="white",
            command=save_event,
            padx=20,
            pady=8
        ).pack(pady=15)

    def delete_item(self):
        selected = self.event_listbox.curselection()
        if not selected:
            messagebox.showwarning("Delete Event", "No event selected.")
            return
        
        idx = selected[0]
        # NEW: Use mapping instead of filtered_events()
        if idx not in self.listbox_index_to_event:
            messagebox.showwarning("Delete Event", "Please select an event to delete.")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event?"):
            event = self.listbox_index_to_event[idx]
            self.schedule.remove(event)
            self.refresh_event_listbox()
            self.save_schedule()

    def open_ai_chat(self):
        # Create AI chat window
        chat_window = tk.Toplevel(self.root)
        chat_window.title("AI Calendar Assistant")
        chat_window.geometry("600x700")
        chat_window.configure(bg="white")
        
        # Header
        header = tk.Frame(chat_window, bg=self.accent_color)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        title = tk.Label(
            header,
            text="🤖 AI Calendar Assistant",
            font=("Segoe UI", 14, "bold"),
            bg=self.accent_color,
            fg="white"
        )
        title.pack(pady=10)
        
        # Chat display area
        chat_display = scrolledtext.ScrolledText(
            chat_window,
            wrap=tk.WORD,
            width=70,
            height=28,
            font=("Segoe UI", 10),
            bg="#f9f9f9",
            fg="#333",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        chat_display.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = tk.Frame(chat_window, bg="white")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        chat_input = tk.Entry(
            input_frame,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            bg="white",
            fg="#333",
            insertbackground=self.button_color
        )
        chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=5)
        
        # Conversation history
        conversation_history = []
        
        def add_message(sender, message):
            chat_display.config(state=tk.NORMAL)
            tag_name = f"{sender}_tag"
            
            if sender == "You":
                chat_display.insert(tk.END, f"{sender}: ", "user_label")
                chat_display.insert(tk.END, f"{message}\n\n", "user_msg")
            else:
                chat_display.insert(tk.END, f"{sender}: ", "assistant_label")
                chat_display.insert(tk.END, f"{message}\n\n", "assistant_msg")
            
            chat_display.tag_config("user_label", foreground=self.button_color, font=("Segoe UI", 10, "bold"))
            chat_display.tag_config("user_msg", foreground="#333", font=("Segoe UI", 10))
            chat_display.tag_config("assistant_label", foreground="#27ae60", font=("Segoe UI", 10, "bold"))
            chat_display.tag_config("assistant_msg", foreground="#333", font=("Segoe UI", 10))
            
            chat_display.see(tk.END)
            chat_display.config(state=tk.DISABLED)
        
        def format_schedule_for_ai():
            """Format the schedule data for the AI to understand"""
            schedule_text = "Current Calendar Events:\n\n"
            
            # Group events by date
            events_by_date = {}
            for event in self.schedule:
                date = event.get("date", "")
                if date not in events_by_date:
                    events_by_date[date] = []
                events_by_date[date].append(event)
            
            # Sort by date and format
            for date in sorted(events_by_date.keys()):
                schedule_text += f"Date: {date}\n"
                for event in events_by_date[date]:
                    event_name = event.get("event", "")
                    start_time = event.get("start_time", "")
                    end_time = event.get("end_time", "")
                    category = event.get("category", "Intellectual")
                    
                    if start_time and end_time:
                        schedule_text += f"  - {start_time} - {end_time}: {event_name} [{category}]\n"
                    elif start_time:
                        schedule_text += f"  - {start_time}: {event_name} [{category}]\n"
                    else:
                        schedule_text += f"  - {event_name} [{category}]\n"
                schedule_text += "\n"
            
            return schedule_text
        
        def send_message():
            user_message = chat_input.get().strip()
            if not user_message:
                return
            
            chat_input.delete(0, tk.END)
            add_message("You", user_message)
            
            # Add to conversation history
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            try:
                # Call Anthropic API
                client = anthropic.Anthropic()
                
                # Build the system prompt with current schedule
                schedule_data = format_schedule_for_ai()
                system_prompt = f"""You are a helpful calendar assistant. You have access to the user's calendar.

{schedule_data}

Your tasks:
1. Help users add new events to their calendar
2. Answer questions about what events are scheduled
3. Tell users if a day is free or busy
4. Help find available time slots

When the user wants to add an event, extract the details and respond with JSON in this EXACT format:
{{
    "action": "add_event",
    "date": "M/D/YY",
    "event": "event description",
    "start_time": "start time (or empty string)",
    "end_time": "end time (or empty string)",
    "category": "Spiritual|Physical|Emotional|Intellectual"
}}

Date format must be M/D/YY (e.g., "1/15/26" for January 15, 2026).

For all other questions about the calendar, respond naturally with helpful information.
If information is missing when adding an event, ask for it in a friendly way."""
                
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=conversation_history
                )
                
                assistant_message = response.content[0].text
                
                # Add to conversation history
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                # Try to parse JSON and add event
                try:
                    # Check if response contains JSON
                    if "{" in assistant_message and "}" in assistant_message:
                        # Extract JSON from response
                        start = assistant_message.find("{")
                        end = assistant_message.rfind("}") + 1
                        json_str = assistant_message[start:end]
                        event_data = json.loads(json_str)
                        
                        if event_data.get("action") == "add_event":
                            # Add event to schedule
                            self.schedule.append({
                                "date": event_data["date"],
                                "event": event_data["event"],
                                "start_time": event_data.get("start_time", ""),
                                "end_time": event_data.get("end_time", ""),
                                "category": event_data.get("category", "Intellectual")
                            })
                            self.refresh_event_listbox()
                            self.save_schedule()
                            add_message("Assistant", f"✓ Event added: {event_data['event']} on {event_data['date']}")
                        else:
                            add_message("Assistant", assistant_message)
                    else:
                        # Normal conversation response
                        add_message("Assistant", assistant_message)
                        
                except json.JSONDecodeError:
                    # Not JSON, just a regular response
                    add_message("Assistant", assistant_message)
                    
            except Exception as e:
                add_message("Assistant", f"Error: {str(e)}\n\nMake sure you have set your ANTHROPIC_API_KEY environment variable.")
        
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=send_message,
            font=("Segoe UI", 10, "bold"),
            bg=self.button_color,
            fg="white",
            padx=20,
            relief=tk.FLAT,
            cursor="hand2"
        )
        send_btn.pack(side=tk.LEFT)
        
        # Bind Enter key
        chat_input.bind("<Return>", lambda e: send_message())
        
        # Welcome message
        add_message("Assistant", "Hi! I'm your calendar assistant. I can help you:\n• Add new events (e.g., 'Add yoga class on January 20th from 6 PM to 7 PM')\n• Check what's scheduled (e.g., 'What do I have on January 22nd?')\n• Find free time (e.g., 'Is January 25th free?')\n• Manage your schedule\n\nWhat would you like to do?")
        
    def get_time_block(self, time_str):
        """Determine which time block an event belongs to"""
        if not time_str:
            return "All Day"
        
        minutes = self.parse_time_for_sorting(time_str)
        if minutes >= 9999:  # Invalid or no time        cd C:\SCHEDULE
            return "All Day"
        
        if minutes < 12 * 60:  # Before noon
            return "Morning"
        elif minutes < 17 * 60:  # Before 5 PM
            return "Afternoon"
        elif minutes < 21 * 60:  # Before 9 PM
            return "Evening"
        else:
            return "Night"

    def refresh_event_listbox(self):
        self.event_listbox.delete(0, tk.END)
        self.listbox_index_to_event = {}  # Reset mapping
        
        # Get filtered events and sort by time
        events = self.filtered_events()
        sorted_events = sorted(events, key=lambda e: self.parse_time_for_sorting(e.get("start_time", "")))
        
        # Group events by time block
        time_blocks = {
            "Morning": [],
            "Afternoon": [],
            "Evening": [],
            "Night": [],
            "All Day": []
        }
        
        for event in sorted_events:
            block = self.get_time_block(event.get("start_time", ""))
            time_blocks[block].append(event)
        
        # Display events by time block with headers
        block_order = ["Morning", "Afternoon", "Evening", "Night", "All Day"]
        block_emojis = {
            "Morning": "🌅",
            "Afternoon": "☀️",
            "Evening": "🌆",
            "Night": "🌙",
            "All Day": "📅"
        }
        
        for block_name in block_order:
            if time_blocks[block_name]:
                # Add time block header
                header = f"{block_emojis[block_name]} {block_name}"
                self.event_listbox.insert(tk.END, header)
                header_idx = self.event_listbox.size() - 1
                self.event_listbox.itemconfig(header_idx, bg="#34495e", fg="white")
                
                # Add events in this time block
                for event in time_blocks[block_name]:
                    event_name = event.get("event", "")
                    start_time = event.get("start_time", "")
                    end_time = event.get("end_time", "")
                    
                    # Build display text based on available time information
                    if start_time and end_time:
                        display_text = f"   🕐 {start_time} - {end_time} — {event_name}"
                    elif start_time:
                        display_text = f"   🕐 {start_time} — {event_name}"
                    else:
                        display_text = f"   {event_name}"
                    
                    self.event_listbox.insert(tk.END, display_text)
                    
                    # Color code by category
                    category = event.get("category", "Intellectual")
                    colors = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Intellectual"])
                    idx = self.event_listbox.size() - 1
                    self.event_listbox.itemconfig(idx, bg=colors["bg"], fg=colors["fg"])
                    
                    # NEW: Store mapping from listbox index to event
                    self.listbox_index_to_event[idx] = event

    def on_date_select(self, event=None):
        self.refresh_event_listbox()
        # Update weather display
        selected_date = self.calendar.get_date()
        weather_info = self.get_weather_for_date(selected_date)
        self.weather_display.config(text=weather_info)

    def filtered_events(self):
        selected_date = self.calendar.get_date()
        return [e for e in self.schedule if e["date"] == selected_date]

    def load_course_schedule(self):
        # Try to load saved data first
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # If no saved data, return default schedule with new categories
        return [
            {"date": "1/19/26", "event": "Study Session - Problem Set Prep", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "1/26/26", "event": "Group Study Meeting", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "1/26/26", "event": "Research Project Work", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/2/26", "event": "Exam Preparation", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/2/26", "event": "Tutorial Session", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/2/26", "event": "Online Course Review", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/9/26", "event": "Case Study Analysis", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/9/26", "event": "Research Documentation", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/9/26", "event": "Learning Module", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/16/26", "event": "Advanced Study", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/16/26", "event": "Project Collaboration", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/23/26", "event": "Final Exam Prep", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "2/24/26", "event": "Team Presentation", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "3/2/26", "event": "Assessment Review", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "3/2/26", "event": "Project Evaluation", "start_time": "", "end_time": "", "category": "Intellectual"},
            {"date": "1/13/26", "event": "Morning Meditation", "start_time": "6:00 AM", "end_time": "6:30 AM", "category": "Spiritual"},
            {"date": "1/15/26", "event": "Yoga Class", "start_time": "7:00 AM", "end_time": "8:00 AM", "category": "Physical"},
            {"date": "1/20/26", "event": "Journaling Session", "start_time": "8:00 PM", "end_time": "8:30 PM", "category": "Emotional"},
            {"date": "1/22/26", "event": "Fitness Training", "start_time": "5:30 PM", "end_time": "6:30 PM", "category": "Physical"},
            {"date": "1/27/26", "event": "Counseling Session", "start_time": "3:00 PM", "end_time": "4:00 PM", "category": "Emotional"},
            {"date": "1/29/26", "event": "Prayer Time", "start_time": "7:00 PM", "end_time": "7:30 PM", "category": "Spiritual"},
            {"date": "2/3/26", "event": "Exercise Class", "start_time": "6:00 PM", "end_time": "7:00 PM", "category": "Physical"},
            {"date": "2/5/26", "event": "Mindfulness Retreat", "start_time": "9:00 AM", "end_time": "5:00 PM", "category": "Spiritual"},
            {"date": "2/10/26", "event": "Running Session", "start_time": "6:00 AM", "end_time": "7:00 AM", "category": "Physical"},
            {"date": "2/12/26", "event": "Wellness Workshop", "start_time": "2:00 PM", "end_time": "4:00 PM", "category": "Emotional"},
            {"date": "2/17/26", "event": "Team Sports", "start_time": "4:00 PM", "end_time": "6:00 PM", "category": "Physical"},
            {"date": "2/19/26", "event": "Spiritual Book Club", "start_time": "7:00 PM", "end_time": "8:30 PM", "category": "Spiritual"},
            {"date": "2/24/26", "event": "Reflection Time", "start_time": "9:00 PM", "end_time": "9:30 PM", "category": "Emotional"},
            {"date": "2/26/26", "event": "Community Meditation", "start_time": "10:00 AM", "end_time": "11:00 AM", "category": "Spiritual"},
        ]
    
    def save_schedule(self):
        """Save schedule to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.schedule, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save data: {str(e)}")
    
    def on_closing(self):
        """Handle window close event"""
        self.save_schedule()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#f5f5f5")
    app = ScheduleApp(root)
    root.mainloop()