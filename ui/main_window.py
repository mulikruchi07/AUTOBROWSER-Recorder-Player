import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import threading, time

from recorder.engine import Recorder
from core.driver_manager import get_driver_with_temp_profile


class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder (Scroll + Wait + Screenshot + Drag)")
        root.geometry("900x600")

        self.driver = None
        self.rec = None

        # LEFT PANEL
        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Button(left, text="Launch Browser", width=25, command=self.launch).pack(pady=5)

        self.url = tk.Entry(left, width=30)
        self.url.insert(0, "https://www.w3schools.com")
        self.url.pack(pady=5)

        tk.Button(left, text="Navigate", width=25, command=self.navigate).pack(pady=5)
        tk.Button(left, text="Start Recording", width=25, command=self.start_record).pack(pady=5)
        tk.Button(left, text="Stop Recording", width=25, command=self.stop_record).pack(pady=5)
        tk.Button(left, text="Play Script", width=25, command=self.play_script).pack(pady=5)
        tk.Button(left, text="Save Script", width=25, command=self.save_script).pack(pady=5)

        # Manual actions
        tk.Label(left, text="Manual Actions:").pack(pady=(10,0))
        tk.Button(left, text="Insert Wait", width=25, command=self.insert_wait).pack(pady=4)
        tk.Button(left, text="Insert Screenshot", width=25, command=self.insert_screenshot).pack(pady=4)

        # Event count
        self.ev_count = tk.StringVar(value="Events: 0")
        tk.Label(left, textvariable=self.ev_count).pack(pady=10)

        # Poller thread updates UI
        threading.Thread(target=self._poller, daemon=True).start()

        # RIGHT — Script list
        self.listbox = tk.Listbox(root, width=100)
        self.listbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)


    # Backend polling for updates
    def _poller(self):
        while True:
            if self.rec:
                script = self.rec.get_script()
                self.ev_count.set(f"Events: {len(script)}")
                self._refresh_list()
            time.sleep(0.5)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        if not self.rec: return

        for ev in self.rec.get_script():
            a = ev["action"]

            if a == "scroll":
                txt = f"SCROLL → x={ev['x']} y={ev['y']}"
            elif a == "wait":
                txt = f"WAIT → {ev['seconds']}s"
            elif a == "screenshot":
                txt = f"SCREENSHOT → {ev['path']}"
            else:
                txt = f"{a.upper()} → {ev.get('selector')}"
            self.listbox.insert(tk.END, txt)

    # Button actions
    def launch(self):
        self.driver = get_driver_with_temp_profile()
        self.rec = Recorder(self.driver)
        messagebox.showinfo("OK", "Browser launched.")

    def navigate(self):
        url = self.url.get().strip()
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
        sec = simpledialog.askfloat("Wait time", "Seconds to wait:", minvalue=0.1)
        if sec:
            self.rec.script.append({"action": "wait", "seconds": sec})

    def insert_screenshot(self):
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if not path: return

        try:
            self.driver.save_screenshot(path)
            self.rec.script.append({"action": "screenshot", "path": path})
        except:
            messagebox.showerror("Error", "Screenshot failed")
