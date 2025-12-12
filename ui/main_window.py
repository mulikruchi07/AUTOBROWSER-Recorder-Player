# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import threading, time, json

from recorder.engine import Recorder
from core.driver_manager import get_driver_with_temp_profile


class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER RECORDER")
        root.geometry("1000x620")

        self.driver = None
        self.rec = None

        # LEFT PANEL
        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Button(left, text="Launch Browser", width=30, command=self.launch).pack(pady=4)

        tk.Label(left, text="URL:").pack(anchor="w")
        self.url_entry = tk.Entry(left, width=34)
        self.url_entry.insert(0, "https://www.w3schools.com")
        self.url_entry.pack(pady=4)

        tk.Button(left, text="Navigate", width=30, command=self.navigate).pack(pady=4)
        tk.Button(left, text="Start Recording", width=30, command=self.start_record).pack(pady=4)
        tk.Button(left, text="Stop Recording", width=30, command=self.stop_record).pack(pady=4)
        tk.Button(left, text="Play Script", width=30, command=self.play_script).pack(pady=4)
        tk.Button(left, text="Save Script", width=30, command=self.save_script).pack(pady=4)
        tk.Button(left, text="Load Script", width=30, command=self.load_script).pack(pady=4)
        tk.Button(left, text="Clear Script", width=30, command=self.clear_script).pack(pady=4)

        # Manual Actions
        tk.Label(left, text="Manual Actions:").pack(pady=(10, 0))
        tk.Button(left, text="Insert Wait", width=30, command=self.insert_wait).pack(pady=3)
        tk.Button(left, text="Insert Screenshot", width=30, command=self.insert_screenshot).pack(pady=3)

        # Status
        self.status = tk.StringVar(value="Status: Idle")
        tk.Label(left, textvariable=self.status, fg="blue").pack(pady=10)

        self.ev_count = tk.StringVar(value="Events: 0")
        tk.Label(left, textvariable=self.ev_count).pack()

        # RIGHT PANEL (Listbox)
        self.listbox = tk.Listbox(root, width=120, height=40)
        self.listbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Background UI thread
        threading.Thread(target=self._update_ui, daemon=True).start()

    def launch(self):
        if self.driver:
            messagebox.showinfo("Browser", "Already launched.")
            return
        self.driver = get_driver_with_temp_profile()
        self.rec = Recorder(self.driver)
        self.status.set("Browser launched")

    def navigate(self):
        url = self.url_entry.get().strip()
        if self.driver:
            self.driver.get(url)
            time.sleep(1)
            self.rec.install_listener()
            self.status.set("Navigated + Listener installed")

    def start_record(self):
        if not self.rec:
            return
        self.rec.start()
        self.status.set("Recording...")

    def stop_record(self):
        if not self.rec:
            return
        self.rec.stop()
        self.status.set("Recording stopped")

    def play_script(self):
        if not self.rec:
            return
        threading.Thread(target=self.rec.play, daemon=True).start()
        self.status.set("Playing script...")

    def save_script(self):
        if not self.rec:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.rec.save(path)
            messagebox.showinfo("Saved", "Script saved.")

    def load_script(self):
        if not self.rec:
            return
        path = filedialog.askopenfilename()
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.rec.script = json.load(f)
            self.status.set("Script loaded")

    def clear_script(self):
        if self.rec:
            self.rec.clear()
            self.status.set("Script cleared")

    # Manual: Insert Wait
    def insert_wait(self):
        if not self.rec:
            return
        sec = simpledialog.askfloat("Wait", "Wait seconds:", minvalue=0.1)
        if sec:
            # PAUSE event recording
            self.rec.pause()

            # Add wait event into script
            self.rec.script.append({"action": "wait", "seconds": float(sec)})

            # Automatically resume after wait
            self.root.after(int(sec * 1000), lambda: self.rec.resume())

    # Manual: Screenshot
    def insert_screenshot(self):
        if not self.rec:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            self.driver.save_screenshot(path)
            self.rec.script.append({"action": "screenshot", "path": path})

    # UI update thread
    def _update_ui(self):
        while True:
            if self.rec:
                self.ev_count.set(f"Events: {len(self.rec.script)}")
                self._refresh_list()
            time.sleep(0.5)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        if not self.rec:
            return

        for ev in self.rec.script:
            act = ev["action"]
            if act == "scroll":
                txt = f"SCROLL → x={ev['x']} y={ev['y']}"
            elif act == "wait":
                txt = f"WAIT → {ev['seconds']}s"
            elif act == "screenshot":
                txt = f"SCREENSHOT → {ev['path']}"
            elif act == "drag":
                txt = f"DRAG → {ev['from']['selector']} → {ev['to']['selector']}"
            elif act == "navigate":
                txt = f"NAVIGATE → {ev['url']}"
            else:
                txt = f"{act.upper()} → {ev.get('selector')}"
            self.listbox.insert(tk.END, txt)
