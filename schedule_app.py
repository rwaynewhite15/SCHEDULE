import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import Calendar

class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Course Schedule Calendar")
        self.schedule = self.load_course_schedule()
        self.create_widgets()

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

    def delete_item(self):
        selected = self.event_listbox.curselection()
        if not selected:
            messagebox.showwarning("Delete Event", "No event selected.")
            return
        idx = selected[0]
        event = self.filtered_events()[idx]
        self.schedule.remove(event)
        self.refresh_event_listbox()

    def open_ai_chat(self):
        messagebox.showinfo("AI Chatbot", "AI Chatbot integration coming soon!")

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
        # Preload your course schedule
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
            # Synchronous Sessions and Virtual Office Hours
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleApp(root)
    root.mainloop()
