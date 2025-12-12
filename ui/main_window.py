# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import threading, time, json
from recorder.engine import Recorder
from core.driver_manager import get_driver_with_temp_profile

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder (stable)")
        root.geometry("960x620")

        self.driver = None
        self.rec = None

        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=8, pady=8)

        tk.Button(left, text="Launch Browser", width=28, command=self.launch).pack(pady=4)

        tk.Label(left, text="URL:").pack(anchor="w")
        self.url_entry = tk.Entry(left, width=36)
        self.url_entry.pack(pady=4)
        self.url_entry.insert(0, "https://jqueryui.com/droppable/")

        tk.Button(left, text="Navigate", width=28, command=self.navigate).pack(pady=4)

        tk.Button(left, text="Start Recording", width=28, command=self.start_record).pack(pady=6)
        tk.Button(left, text="Stop Recording", width=28, command=self.stop_record).pack(pady=6)
        tk.Button(left, text="Test Listener", width=28, command=self.test_listener).pack(pady=6)

        tk.Button(left, text="Play Script", width=28, command=self.play_script).pack(pady=6)
        tk.Button(left, text="Save Script", width=28, command=self.save_script).pack(pady=6)
        tk.Button(left, text="Load Script", width=28, command=self.load_script).pack(pady=6)
        tk.Button(left, text="Clear Script", width=28, command=self.clear_script).pack(pady=6)

        tk.Label(left, text="Manual actions:").pack(pady=(12,0))
        tk.Button(left, text="Insert Wait", width=28, command=self.insert_wait).pack(pady=4)
        tk.Button(left, text="Insert Screenshot", width=28, command=self.insert_screenshot).pack(pady=4)

        # status & event count
        self.status_var = tk.StringVar(value="No browser")
        tk.Label(left, textvariable=self.status_var, fg="blue").pack(pady=(12,0))
        self.event_count_var = tk.StringVar(value="Events: 0")
        tk.Label(left, textvariable=self.event_count_var).pack()

        right = tk.Frame(root)
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        tk.Label(right, text="Recorded Script").pack()
        self.listbox = tk.Listbox(right, width=120, height=36)
        self.listbox.pack(fill="both", expand=True)

        # UI updater thread
        threading.Thread(target=self._ui_updater, daemon=True).start()

    def launch(self):
        if self.driver:
            messagebox.showinfo("Info", "Browser already launched")
            return
        try:
            self.driver = get_driver_with_temp_profile()
            self.rec = Recorder(self.driver)
            self.status_var.set("Browser launched")
            messagebox.showinfo("OK", "Browser launched")
        except Exception as e:
            messagebox.showerror("Launch failed", str(e))
            self.status_var.set("Launch failed")

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
            try:
                self.rec.install_listener()
                self.status_var.set("Listener installed on page")
            except Exception:
                self.status_var.set("Listener installation attempted")
        except Exception as e:
            messagebox.showerror("Navigation error", str(e))

    def start_record(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        try:
            self.rec.start()
            self.status_var.set("Recording...")
        except Exception as e:
            messagebox.showerror("Start error", str(e))

    def stop_record(self):
        if not self.rec:
            return
        try:
            self.rec.stop()
            self.status_var.set("Recording stopped")
            self._refresh_list()
        except Exception as e:
            messagebox.showerror("Stop error", str(e))

    def test_listener(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        try:
            js = "window.top.__AUTOBROWSER_EVENTS__ = window.top.__AUTOBROWSER_EVENTS__ || []; window.top.__AUTOBROWSER_EVENTS__.push({action:'_test', ts:Date.now()});"
            try:
                self.driver.execute_script(js)
            except Exception:
                pass
            time.sleep(0.35)
            evs = self.rec.get_script()
            found = any(e.get('action') == '_test' for e in evs)
            if found:
                self.status_var.set("Listener OK (test detected)")
                messagebox.showinfo("Test Listener", "OK — test event detected")
            else:
                self.status_var.set("Listener not detected")
                messagebox.showwarning("Test Listener", "No test event seen yet. Try navigate then Test Listener.")
        except Exception as e:
            messagebox.showerror("Test error", str(e))

    def play_script(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch + record or load a script first")
            return
        threading.Thread(target=self._play_thread, daemon=True).start()

    def _play_thread(self):
        try:
            self.status_var.set("Playing script...")
            self.rec.play()
            self.status_var.set("Play finished")
        except Exception as e:
            messagebox.showerror("Play error", str(e))
            self.status_var.set("Play error")

    def save_script(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch + record first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        try:
            self.rec.save(path)
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def load_script(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.rec.script = data
            self._refresh_list()
            messagebox.showinfo("Loaded", path)
        except Exception as e:
            messagebox.showerror("Load error", str(e))

    def clear_script(self):
        if not self.rec:
            return
        self.rec.clear()
        self._refresh_list()
        self.status_var.set("Script cleared")

    def insert_wait(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        sec = simpledialog.askfloat("Wait seconds", "Seconds to wait:", minvalue=0.1, initialvalue=1.0)
        if sec is None:
            return
        # ensure float typed
        self.rec.script.append({"action": "wait", "seconds": float(sec)})
        self._refresh_list()

    def insert_screenshot(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if not path:
            return
        try:
            self.driver.save_screenshot(path)
            self.rec.script.append({"action": "screenshot", "path": path})
            self._refresh_list()
        except Exception as e:
            messagebox.showerror("Screenshot error", str(e))

    # UI updater
    def _ui_updater(self):
        while True:
            try:
                if self.rec:
                    cnt = len(self.rec.get_script())
                    self.event_count_var.set(f"Events: {cnt}")
                    self._refresh_list()
            except Exception:
                pass
            time.sleep(0.5)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        if not self.rec:
            return
        for i, ev in enumerate(self.rec.get_script()):
            a = ev.get("action")
            if a == "scroll":
                txt = f"{i}: SCROLL -> x={ev.get('x')} y={ev.get('y')}"
            elif a == "wait":
                txt = f"{i}: WAIT -> {ev.get('seconds')}s"
            elif a == "screenshot":
                txt = f"{i}: SCREENSHOT -> {ev.get('path')}"
            elif a == "drag":
                txt = f"{i}: DRAG -> {ev.get('from', {}).get('selector')} -> {ev.get('to', {}).get('selector')}"
            elif a == "navigate":
                txt = f"{i}: NAVIGATE -> {ev.get('url')}"
            else:
                txt = f"{i}: {a.upper()} -> {ev.get('selector')}"
            self.listbox.insert(tk.END, txt)
