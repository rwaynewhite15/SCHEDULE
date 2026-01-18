import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from tkcalendar import Calendar
import anthropic
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Course Schedule Calendar")
        self.data_file = "calendar_data.json"
        self.schedule = self.load_course_schedule()
        self.create_widgets()
        
        # Save on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        cal_frame = tk.Frame(self.root)
        cal_frame.pack(pady=10)

        self.calendar = Calendar(cal_frame, selectmode='day', year=2026, month=1, day=15)
        self.calendar.pack(side=tk.LEFT, padx=10)

        self.event_listbox = tk.Listbox(cal_frame, width=50, height=15)
        self.event_listbox.pack(side=tk.LEFT, padx=10)

        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        add_btn = tk.Button(btn_frame, text="Add Event", command=self.add_item)
        add_btn.grid(row=0, column=0, padx=5)

        edit_btn = tk.Button(btn_frame, text="Edit Event", command=self.edit_item)
        edit_btn.grid(row=0, column=1, padx=5)

        del_btn = tk.Button(btn_frame, text="Delete Event", command=self.delete_item)
        del_btn.grid(row=0, column=2, padx=5)

        ai_btn = tk.Button(btn_frame, text="AI Chatbot", command=self.open_ai_chat)
        ai_btn.grid(row=0, column=3, padx=5)

        self.refresh_event_listbox()

    def add_item(self):
        date = self.calendar.get_date()
        item = simpledialog.askstring("Add Event", f"Enter event for {date}:")
        if item:
            self.schedule.append({"date": date, "event": item})
            self.refresh_event_listbox()
            self.save_schedule()

    def edit_item(self):
        selected = self.event_listbox.curselection()
        if not selected:
            messagebox.showwarning("Edit Event", "No event selected.")
            return
        idx = selected[0]
        event = self.filtered_events()[idx]
        new_event = simpledialog.askstring("Edit Event", "Edit event:", initialvalue=event["event"])
        if new_event:
            event["event"] = new_event
            self.refresh_event_listbox()
            self.save_schedule()

    def delete_item(self):
        selected = self.event_listbox.curselection()
        if not selected:
            messagebox.showwarning("Delete Event", "No event selected.")
            return
        idx = selected[0]
        event = self.filtered_events()[idx]
        self.schedule.remove(event)
        self.refresh_event_listbox()
        self.save_schedule()

    def open_ai_chat(self):
        # Create AI chat window
        chat_window = tk.Toplevel(self.root)
        chat_window.title("AI Calendar Assistant")
        chat_window.geometry("500x600")
        
        # Chat display area
        chat_display = scrolledtext.ScrolledText(chat_window, wrap=tk.WORD, width=60, height=25)
        chat_display.pack(padx=10, pady=10)
        chat_display.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = tk.Frame(chat_window)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        chat_input = tk.Entry(input_frame, width=45)
        chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Conversation history
        conversation_history = []
        
        def add_message(sender, message):
            chat_display.config(state=tk.NORMAL)
            chat_display.insert(tk.END, f"{sender}: {message}\n\n")
            chat_display.see(tk.END)
            chat_display.config(state=tk.DISABLED)
        
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
                
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    system="""You are a helpful calendar assistant. Help users add events to their calendar.

When the user wants to add an event, extract the details and respond with JSON in this EXACT format:
{
    "action": "add_event",
    "date": "M/D/YY",
    "event": "event description"
}

Date format must be M/D/YY (e.g., "1/15/26" for January 15, 2026).
If information is missing, ask for it in a friendly way.
If the user is just chatting or asking questions, respond normally without JSON.""",
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
                                "event": event_data["event"]
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
        
        send_btn = tk.Button(input_frame, text="Send", command=send_message)
        send_btn.pack(side=tk.LEFT)
        
        # Bind Enter key
        chat_input.bind("<Return>", lambda e: send_message())
        
        # Welcome message
        add_message("Assistant", "Hi! I'm your calendar assistant. You can ask me to add events like 'Add a dentist appointment on January 20th' or 'Schedule study session for next Tuesday at 3pm'.")

    def refresh_event_listbox(self):
        self.event_listbox.delete(0, tk.END)
        for event in self.filtered_events():
            self.event_listbox.insert(tk.END, event["event"])

    def on_date_select(self, event=None):
        self.refresh_event_listbox()

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
        
        # If no saved data, return default course schedule
        return [
            {"date": "1/19/26", "event": "Flow Diagram (team) Due"},
            {"date": "1/26/26", "event": "Problem Set 1 (individual) Due"},
            {"date": "1/26/26", "event": "Case Report 1: Benihana (team) Due"},
            {"date": "2/2/26", "event": "Quiz 1 (individual) Due"},
            {"date": "2/2/26", "event": "Quiz 1: Manzana (individual) Due"},
            {"date": "2/2/26", "event": "Problem Set 2 (individual) Due"},
            {"date": "2/9/26", "event": "Case Quiz 2: Playa Dorado (individual) Due"},
            {"date": "2/9/26", "event": "Problem Set 3 (individual) Due"},
            {"date": "2/9/26", "event": "Quiz 2 (individual) Due"},
            {"date": "2/16/26", "event": "Problem Set 4 (individual) Due"},
            {"date": "2/16/26", "event": "Case Report 2: Sport Obermeyer (team) Due"},
            {"date": "2/23/26", "event": "Case Quiz 3: TPS and Toyota Case Quiz (individual) Due"},
            {"date": "2/24/26", "event": "Project Presentation & Report (team) Due"},
            {"date": "3/2/26", "event": "Final Quiz (individual) Due"},
            {"date": "3/2/26", "event": "Project Peer Feedback (individual) Due"},
            {"date": "1/13/26", "event": "Sync Session: Course Introduction"},
            {"date": "1/15/26", "event": "Virtual Office Hour"},
            {"date": "1/20/26", "event": "Sync Session: Course Project & Benihana Simulation Introduction"},
            {"date": "1/22/26", "event": "Virtual Office Hour"},
            {"date": "1/27/26", "event": "Virtual Office Hour"},
            {"date": "1/29/26", "event": "Sync Session: Manzana Insurance Case"},
            {"date": "2/3/26", "event": "Virtual Office Hour"},
            {"date": "2/5/26", "event": "Sync Session: Playa Dorado Case"},
            {"date": "2/10/26", "event": "Virtual Office Hour"},
            {"date": "2/12/26", "event": "Sync Session: Sport Obermeyer Case"},
            {"date": "2/17/26", "event": "Virtual Office Hour"},
            {"date": "2/19/26", "event": "Sync Session: Toyota & Hank Kolb"},
            {"date": "2/24/26", "event": "Sync Session: Bullwhip Effect"},
            {"date": "2/26/26", "event": "Virtual Office Hour"},
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
    app = ScheduleApp(root)
    root.mainloop()