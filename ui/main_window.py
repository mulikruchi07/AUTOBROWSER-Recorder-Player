# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading, time
from core.driver_manager import get_driver_with_temp_profile
from recorder.recorder import Recorder

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder & Player (CDP-injection)")
        root.geometry("920x620")

        self.driver = None
        self.rec = None
        self.polling = False

        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=8, pady=8)

        tk.Button(left, text="Launch Browser", width=26, command=self.launch).pack(pady=6)

        tk.Label(left, text="URL:").pack(anchor="w")
        self.url_entry = tk.Entry(left, width=36)
        self.url_entry.pack(pady=4)
        self.url_entry.insert(0,"https://www.redbus.in")
        tk.Button(left, text="Navigate", width=26, command=self.navigate).pack(pady=4)

        self.start_btn = tk.Button(left, text="Start Recording", width=26, state="disabled", command=self.start_record)
        self.start_btn.pack(pady=6)
        self.stop_btn = tk.Button(left, text="Stop Recording", width=26, state="disabled", command=self.stop_record)
        self.stop_btn.pack(pady=6)

        tk.Button(left, text="Play Script", width=26, command=self.play_script).pack(pady=6)
        tk.Button(left, text="Save Script", width=26, command=self.save_script).pack(pady=6)
        tk.Button(left, text="Load Script", width=26, command=self.load_script).pack(pady=6)
        tk.Button(left, text="Clear Script", width=26, command=self.clear_script).pack(pady=6)

        tk.Label(left, text="Manual actions:").pack(pady=(12,0))
        tk.Button(left, text="Insert Wait", width=26, command=self.insert_wait).pack(pady=4)
        tk.Button(left, text="Insert Screenshot", width=26, command=self.insert_screenshot).pack(pady=4)
        tk.Button(left, text="Insert Scroll (current)", width=26, command=self.insert_scroll).pack(pady=4)

        right = tk.Frame(root)
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        tk.Label(right, text="Recorded Script").pack()
        self.listbox = tk.Listbox(right, width=110, height=34)
        self.listbox.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="No browser")
        tk.Label(root, textvariable=self.status_var, anchor="w").pack(side="bottom", fill="x")

    def set_status(self, txt):
        self.status_var.set(txt)

    def launch(self):
        if self.driver:
            messagebox.showinfo("Info","Browser already launched")
            return
        self.set_status("Launching browser...")
        try:
            self.driver = get_driver_with_temp_profile()
            self.rec = Recorder(self.driver)
            # install listener persistently upfront
            try:
                self.rec.install_listener()
            except Exception:
                pass
            self.start_btn.config(state="normal")
            self.set_status("Browser launched; listener installed")
        except Exception as e:
            messagebox.showerror("Launch error", str(e))
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
            # ensure listener re-injection
            try:
                self.rec.install_listener()
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
        self.stop_btn.config(state="disabled")
        self.start_btn.config(state="normal")
        self.update_list()
        self.set_status("Stopped recording")

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
        for i,s in enumerate(script):
            self.listbox.insert(tk.END, self._format(s,i))

    def _format(self,s,i):
        a=s.get('action')
        if a=='click': return f"{i}: CLICK -> {s.get('selector')}"
        if a=='type': return f"{i}: TYPE -> {s.get('selector')} = {s.get('value')}"
        if a=='scroll': return f"{i}: SCROLL -> x={s.get('x')} y={s.get('y')}"
        if a=='wait': return f"{i}: WAIT -> {s.get('seconds')}s"
        if a=='screenshot': return f"{i}: SCREENSHOT -> {s.get('path')}"
        if a=='navigate': return f"{i}: NAVIGATE -> {s.get('url')}"
        if a in ('dragstart','dragend'): return f"{i}: {a.upper()} -> {s.get('selector')}"
        if a=='navigate_marker': return f"{i}: NAV_MARKER -> {s.get('url')}"
        return f"{i}: {a} -> {s}"

    def play_script(self):
        if not self.rec:
            messagebox.showwarning("No script", "Record or load a script first")
            return
        self.set_status("Playing...")
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
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path: return
        try:
            self.rec.save(path)
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def load_script(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not path: return
        try:
            if not self.rec:
                self.rec = Recorder(None)
            self.rec.load(path)
            self.update_list()
            messagebox.showinfo("Loaded", f"Loaded {path}")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))

    def clear_script(self):
        if not self.rec: return
        self.rec.clear()
        self.update_list()

    def insert_wait(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        sec = simpledialog.askfloat("Wait seconds", "Seconds:", minvalue=0.1, initialvalue=1.0)
        if sec is None: return
        self.rec.add_wait(sec)
        self.update_list()

    def insert_screenshot(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if not path: return
        p = self.rec.add_screenshot(path=path)
        if p:
            messagebox.showinfo("Screenshot", f"Saved {p}")
            self.update_list()
        else:
            messagebox.showerror("Screenshot failed", "Could not take screenshot")

    def insert_scroll(self):
        if not self.rec:
            messagebox.showwarning("No recorder", "Launch browser first")
            return
        self.rec.add_scroll()
        self.update_list()
