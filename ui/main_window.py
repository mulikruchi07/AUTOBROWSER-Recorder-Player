# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading, time, os
from core.driver_manager import get_driver_with_temp_profile
from recorder.recorder import Recorder

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder & Player (Enhanced)")
        root.geometry("900x620")

        self.driver = None
        self.rec = None
        self.polling = False

        # Left panel
        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=8, pady=8)

        tk.Button(left, text="Launch Browser", width=24, command=self.launch).pack(pady=6)

        tk.Label(left, text="URL:").pack(anchor="w")
        self.url_entry = tk.Entry(left, width=34)
        self.url_entry.pack(pady=4)
        self.url_entry.insert(0,"https://www.redbus.in")
        tk.Button(left, text="Navigate", width=24, command=self.navigate).pack(pady=4)

        self.start_btn = tk.Button(left, text="Start Recording", width=24, state="disabled", command=self.start_record)
        self.start_btn.pack(pady=6)
        self.stop_btn = tk.Button(left, text="Stop Recording", width=24, state="disabled", command=self.stop_record)
        self.stop_btn.pack(pady=6)

        tk.Button(left, text="Play Script", width=24, command=self.play_script).pack(pady=6)
        tk.Button(left, text="Save Script", width=24, command=self.save_script).pack(pady=6)
        tk.Button(left, text="Load Script", width=24, command=self.load_script).pack(pady=6)
        tk.Button(left, text="Clear Script", width=24, command=self.clear_script).pack(pady=6)

        tk.Label(left, text="Manual actions:").pack(pady=(12,0))
        tk.Button(left, text="Insert Wait", width=24, command=self.insert_wait).pack(pady=4)
        tk.Button(left, text="Insert Screenshot", width=24, command=self.insert_screenshot).pack(pady=4)
        tk.Button(left, text="Insert Scroll (current)", width=24, command=self.insert_scroll).pack(pady=4)

        # Right panel (script)
        right = tk.Frame(root)
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        tk.Label(right, text="Recorded Script").pack()
        self.listbox = tk.Listbox(right, width=100, height=32)
        self.listbox.pack(fill="both", expand=True)

        # Status bar
        self.status = tk.StringVar(value="No browser launched")
        tk.Label(root, textvariable=self.status, anchor="w").pack(side="bottom", fill="x")

    def set_status(self, text):
        self.status.set(text)

    def launch(self):
        if self.driver:
            messagebox.showinfo("Info","Browser already launched")
            return
        self.set_status("Launching browser...")
        try:
            self.driver = get_driver_with_temp_profile()
            self.rec = Recorder(self.driver)
            self.start_btn.config(state="normal")
            self.set_status("Browser launched")
        except Exception as e:
            messagebox.showerror("Launch failed", str(e))
            self.set_status("Launch failed")

    def navigate(self):
        if not self.driver:
            messagebox.showwarning("No browser", "Launch browser first")
            return
        url = self.url_entry.get().strip()
        if not url:
            return
        try:
            self.driver.get(url)
            time.sleep(0.8)
            # inject listener after navigation
            try:
                self.rec.inject()
            except Exception:
                pass
            self.set_status(f"Navigated to {url}")
        except Exception as e:
            messagebox.showerror("Navigation error", str(e))

    def start_record(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        self.rec.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.polling = True
        threading.Thread(target=self._ui_poller, daemon=True).start()
        self.set_status("Recording...")

    def stop_record(self):
        if not self.rec:
            return
        self.rec.stop()
        self.polling = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.update_list()
        self.set_status("Recording stopped")

    def _ui_poller(self):
        while self.polling:
            try:
                self.update_list()
            except Exception:
                pass
            time.sleep(0.5)

    def update_list(self):
        if not self.rec:
            return
        script = self.rec.get_script()
        self.listbox.delete(0, tk.END)
        for i, s in enumerate(script):
            display = self._format_step(s, i)
            self.listbox.insert(tk.END, display)

    def _format_step(self, s, idx):
        a = s.get('action')
        if a == 'click':
            return f"{idx}: CLICK -> {s.get('selector')}"
        if a == 'type':
            return f"{idx}: TYPE -> {s.get('selector')} = {s.get('value')}"
        if a == 'scroll':
            return f"{idx}: SCROLL -> x={s.get('x')} y={s.get('y')}"
        if a == 'wait':
            return f"{idx}: WAIT -> {s.get('seconds')}s"
        if a == 'screenshot':
            return f"{idx}: SCREENSHOT -> {s.get('path')}"
        if a == 'navigate':
            return f"{idx}: NAVIGATE -> {s.get('url')}"
        if a in ('dragstart','dragend'):
            return f"{idx}: {a.upper()} -> {s.get('selector')}"
        if a == 'navigate_marker':
            return f"{idx}: NAV_MARKER -> {s.get('url')}"
        return f"{idx}: {a} -> {s}"

    def play_script(self):
        if not self.rec:
            messagebox.showwarning("No script", "Load or record a script first")
            return
        self.set_status("Playing script...")
        threading.Thread(target=self._play_thread, daemon=True).start()

    def _play_thread(self):
        try:
            self.rec.play(delay_between=0.7)
            self.set_status("Play finished")
        except Exception as e:
            self.set_status("Play error: "+str(e))

    def save_script(self):
        if not self.rec:
            messagebox.showwarning("No script", "Record or load script first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path:
            return
        try:
            self.rec.save(path)
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def load_script(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not path:
            return
        try:
            if not self.rec:
                # create recorder with dummy driver if not launched
                self.rec = Recorder(None)
            self.rec.load(path)
            self.update_list()
            messagebox.showinfo("Loaded", f"Loaded {path}")
        except Exception as e:
            messagebox.showerror("Load error", str(e))

    def clear_script(self):
        if not self.rec:
            return
        self.rec.clear()
        self.update_list()

    # manual insertions
    def insert_wait(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        val = simpledialog.askfloat("Wait", "Seconds to wait:", minvalue=0.1, initialvalue=1.0)
        if val is None:
            return
        self.rec.add_wait(val)
        self.update_list()

    def insert_screenshot(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        # ask for filename
        fname = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if not fname:
            return
        p = self.rec.add_screenshot(path=fname)
        if p:
            messagebox.showinfo("Screenshot", f"Saved: {p}")
            self.update_list()
        else:
            messagebox.showerror("Error", "Could not take screenshot")

    def insert_scroll(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        self.rec.add_scroll()
        self.update_list()
