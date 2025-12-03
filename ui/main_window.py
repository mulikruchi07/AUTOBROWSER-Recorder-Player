# ui/main_window.py
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
from core.driver_manager import get_driver_with_temp_profile
from recorder.recorder import Recorder

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder & Player")
        root.geometry("820x560")
        self.driver = None
        self.recorder = None
        self.polling_ui = False

        # Left frame: controls
        lf = tk.Frame(root)
        lf.pack(side="left", fill="y", padx=8, pady=8)

        self.launch_btn = tk.Button(lf, text="Launch Browser", width=20, command=self.launch_browser)
        self.launch_btn.pack(pady=6)

        self.nav_entry = tk.Entry(lf, width=28)
        self.nav_entry.pack(pady=4)
        self.nav_entry.insert(0, "https://www.redbus.in")
        tk.Button(lf, text="Navigate", width=20, command=self.navigate_to_url).pack(pady=4)

        self.start_rec_btn = tk.Button(lf, text="Start Recording", width=20, command=self.start_recording, state="disabled")
        self.start_rec_btn.pack(pady=6)
        self.stop_rec_btn = tk.Button(lf, text="Stop Recording", width=20, command=self.stop_recording, state="disabled")
        self.stop_rec_btn.pack(pady=6)

        tk.Button(lf, text="Play Script", width=20, command=self.play_script, state="disabled").pack(pady=6)
        tk.Button(lf, text="Save Script", width=20, command=self.save_script, state="disabled").pack(pady=6)
        tk.Button(lf, text="Load Script", width=20, command=self.load_script).pack(pady=6)
        tk.Button(lf, text="Clear Script", width=20, command=self.clear_script).pack(pady=6)
        tk.Button(lf, text="Take Screenshot", width=20, command=self.take_screenshot, state="disabled").pack(pady=6)

        # Right frame: script view
        rf = tk.Frame(root)
        rf.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        tk.Label(rf, text="Recorded Steps").pack()
        self.listbox = tk.Listbox(rf, width=80, height=30)
        self.listbox.pack(fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="No browser")
        status = tk.Label(root, textvariable=self.status_var, anchor="w")
        status.pack(side="bottom", fill="x")

    def set_status(self, txt):
        self.status_var.set(txt)

    def launch_browser(self):
        if self.driver:
            messagebox.showinfo("Browser", "Browser already launched.")
            return
        self.set_status("Launching Chrome...")
        try:
            self.driver = get_driver_with_temp_profile()
            self.recorder = Recorder(self.driver)
            self.set_status("Browser launched. Ready.")
            self.start_rec_btn.config(state="normal")
            self.stop_rec_btn.config(state="disabled")
            for child in self.root.winfo_children():
                pass
            # enable play/save/take screenshot
            self.enable_buttons_after_launch(True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch browser: {e}")
            self.set_status("Launch failed.")

    def enable_buttons_after_launch(self, enabled=True):
        state = "normal" if enabled else "disabled"
        self.start_rec_btn.config(state=state)
        self.stop_rec_btn.config(state="disabled")
        # find Save/Play/Screenshot buttons by traversal
        for widget in self.root.winfo_children():
            pass
        # manually enable later via methods
        # set take screenshot button
        for child in self.root.pack_slaves():
            pass
        # set generic
        # easier to find by iterating all buttons
        for w in self.root.winfo_children():
            for sub in getattr(w, "winfo_children", lambda: [])():
                if isinstance(sub, tk.Button) and sub.cget("text") in ("Play Script","Save Script","Take Screenshot"):
                    sub.config(state=state)

    def navigate_to_url(self):
        if not self.driver:
            messagebox.showwarning("No browser", "Launch browser first.")
            return
        url = self.nav_entry.get().strip()
        if not url:
            return
        try:
            self.driver.get(url)
            self.set_status(f"Opened {url}")
            # inject listener so user can click and record
            try:
                self.recorder.start_inject()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Navigation error", str(e))

    def start_recording(self):
        if not self.recorder:
            messagebox.showwarning("No browser", "Launch browser first.")
            return
        self.recorder.start_recording()
        self.set_status("Recording...")
        self.start_rec_btn.config(state="disabled")
        self.stop_rec_btn.config(state="normal")
        # start UI poller to update listbox
        self.polling_ui = True
        threading.Thread(target=self._ui_poller_thread, daemon=True).start()

    def stop_recording(self):
        if not self.recorder:
            return
        self.recorder.stop_recording()
        self.set_status("Recording stopped.")
        self.start_rec_btn.config(state="normal")
        self.stop_rec_btn.config(state="disabled")
        self.polling_ui = False
        self.update_listbox_from_script()

    def _ui_poller_thread(self):
        while self.polling_ui:
            self.root.after(0, self.update_listbox_from_script)
            time.sleep(0.8)

    def update_listbox_from_script(self):
        if not self.recorder:
            return
        script = self.recorder.get_script()
        self.listbox.delete(0, tk.END)
        for i, a in enumerate(script):
            txt = self._action_to_string(a, index=i)
            self.listbox.insert(tk.END, txt)

    def _action_to_string(self, a, index=None):
        act = a.get("action")
        if act == "click":
            return f"{index or ''} CLICK -> {a.get('selector')}"
        if act == "type":
            return f"{index or ''} TYPE -> {a.get('selector')} = {a.get('value')}"
        if act == "navigate":
            return f"{index or ''} NAVIGATE -> {a.get('url')}"
        if act == "wait":
            return f"{index or ''} WAIT -> {a.get('seconds')}s"
        return f"{index or ''} {json.dumps(a)}"

    def play_script(self):
        if not self.recorder:
            messagebox.showwarning("No browser", "Launch browser first.")
            return
        # disable UI while playing
        self.set_status("Playing script...")
        t = threading.Thread(target=self._play_thread, daemon=True)
        t.start()

    def _play_thread(self):
        try:
            # enable Play button only when script exists
            self.recorder.play_script(delay_between=0.8)
            self.set_status("Script execution finished.")
        except Exception as e:
            self.set_status(f"Play error: {e}")

    def save_script(self):
        if not self.recorder:
            messagebox.showwarning("No browser", "Launch browser first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not path:
            return
        try:
            self.recorder.save_script_to_file(path)
            messagebox.showinfo("Saved", f"Script saved to {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def load_script(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not path:
            return
        try:
            if not self.recorder:
                # still allow loading without launching browser
                from recorder.recorder import Recorder
                # create a dummy driver? not needed for loading; create recorder with None
                self.recorder = Recorder(None)
            self.recorder.load_script_from_file(path)
            self.update_listbox_from_script()
            messagebox.showinfo("Loaded", f"Script loaded from {path}")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))

    def clear_script(self):
        if not self.recorder:
            return
        self.recorder.clear_script()
        self.update_listbox_from_script()

    def take_screenshot(self):
        if not self.driver:
            messagebox.showwarning("No browser", "Launch browser first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if not path:
            return
        try:
            self.driver.save_screenshot(path)
            messagebox.showinfo("Screenshot", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Screenshot error", str(e))

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
