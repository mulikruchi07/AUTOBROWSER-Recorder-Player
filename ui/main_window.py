import tkinter as tk
from tkinter import filedialog, messagebox
import threading, time
from recorder.engine import Recorder
from core.driver_manager import get_driver_with_temp_profile

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder")
        root.geometry("900x600")

        self.driver = None
        self.rec = None

        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Button(left, text="Launch Browser", width=25, command=self.launch).pack(pady=4)

        self.url = tk.Entry(left, width=30)
        self.url.insert(0, "https://www.w3schools.com/html/html_forms.asp")
        self.url.pack(pady=4)

        tk.Button(left, text="Navigate", width=25, command=self.navigate).pack(pady=4)
        tk.Button(left, text="Start Recording", width=25, command=self.start_record).pack(pady=4)
        tk.Button(left, text="Stop Recording", width=25, command=self.stop_record).pack(pady=4)
        tk.Button(left, text="Save Script", width=25, command=self.save_script).pack(pady=4)

        self.event_count = tk.StringVar(value="Events: 0")
        tk.Label(left, textvariable=self.event_count).pack(pady=10)

        threading.Thread(target=self._event_count_poller, daemon=True).start()

        self.listbox = tk.Listbox(root, width=100)
        self.listbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def _event_count_poller(self):
        while True:
            if self.rec:
                self.event_count.set(f"Events: {len(self.rec.get_script())}")
                self._refresh_list()
            time.sleep(0.5)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        if not self.rec: return
        for ev in self.rec.get_script():
            self.listbox.insert(tk.END, f"{ev['action']} → {ev.get('selector')}")

    def launch(self):
        self.driver = get_driver_with_temp_profile()
        self.rec = Recorder(self.driver)
        messagebox.showinfo("OK", "Browser launched")

    def navigate(self):
        url = self.url.get().strip()
        self.driver.get(url)
        self.rec.install_listener()

    def start_record(self):
        self.rec.start()

    def stop_record(self):
        self.rec.stop()

    def save_script(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.rec.save(path)
            messagebox.showinfo("Saved", path)
