# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading, time

from recorder.engine import Recorder
from core.driver_manager import get_driver_with_temp_profile

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder (Scroll + Wait Enabled)")
        root.geometry("900x600")

        self.driver = None
        self.rec = None

        # Left panel
        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Button(left, text="Launch Browser", width=25, command=self.launch).pack(pady=4)

        self.url_entry = tk.Entry(left, width=30)
        self.url_entry.insert(0, "https://www.w3schools.com/html/html_forms.asp")
        self.url_entry.pack(pady=4)

        tk.Button(left, text="Navigate", width=25, command=self.navigate).pack(pady=4)
        tk.Button(left, text="Start Recording", width=25, command=self.start_record).pack(pady=4)
        tk.Button(left, text="Stop Recording", width=25, command=self.stop_record).pack(pady=4)
        tk.Button(left, text="Play Script", width=25, command=self.play_script).pack(pady=4)
        tk.Button(left, text="Save Script", width=25, command=self.save_script).pack(pady=4)

        # --- MANUAL ACTIONS ---
        tk.Label(left, text="Manual Actions:").pack(pady=(10,2))
        tk.Button(left, text="Insert Wait", width=25, command=self.insert_wait).pack(pady=4)

        self.event_label = tk.StringVar(value="Events: 0")
        tk.Label(left, textvariable=self.event_label).pack(pady=10)

        # Start UI poller
        threading.Thread(target=self._event_poller, daemon=True).start()

        # Right list box
        self.listbox = tk.Listbox(root, width=100)
        self.listbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # Event polling for UI updates
    def _event_poller(self):
        while True:
            if self.rec:
                script = self.rec.get_script()
                self.event_label.set(f"Events: {len(script)}")
                self._refresh_list()
            time.sleep(0.5)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        if not self.rec:
            return

        for ev in self.rec.get_script():
            a = ev["action"]
            if a == "scroll":
                txt = f"SCROLL → x={ev['x']} y={ev['y']}"
            elif a == "wait":
                txt = f"WAIT → {ev['seconds']}s"
            else:
                txt = f"{a.upper()} → {ev.get('selector')}"
            self.listbox.insert(tk.END, txt)

    # BUTTON ACTIONS
    def launch(self):
        self.driver = get_driver_with_temp_profile()
        self.rec = Recorder(self.driver)
        messagebox.showinfo("OK", "Browser launched")

    def navigate(self):
        url = self.url_entry.get().strip()
        self.driver.get(url)
        self.rec.install_listener()

    def start_record(self):
        self.rec.start()

    def stop_record(self):
        self.rec.stop()

    def play_script(self):
        threading.Thread(target=self.rec.play, daemon=True).start()

    def save_script(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.rec.save(path)
            messagebox.showinfo("Saved", path)

    def insert_wait(self):
        sec = simpledialog.askfloat("Wait Duration", "Seconds to wait:", minvalue=0.1, initialvalue=1.0)
        if sec:
            self.rec.script.append({"action": "wait", "seconds": sec})
