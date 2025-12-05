import time
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from core.driver_manager import get_driver_with_temp_profile
from recorder.recorder import Recorder

class App:
    def __init__(self, root):
        self.root = root
        root.title("AUTOBROWSER Recorder & Player")
        root.geometry("830x560")

        self.driver = None
        self.rec = None
        self.polling = False

        # Left UI
        left = tk.Frame(root)
        left.pack(side="left", fill="y", padx=8, pady=8)

        tk.Button(left, text="Launch Browser", width=22, command=self.launch).pack(pady=6)

        tk.Label(left, text="Navigate URL:").pack()
        self.url = tk.Entry(left, width=30)
        self.url.pack(pady=3)
        self.url.insert(0, "https://www.redbus.in")
        tk.Button(left, text="Go", command=self.go).pack(pady=4)

        self.start_btn = tk.Button(left, text="Start Recording", width=22, command=self.start, state="disabled")
        self.start_btn.pack(pady=6)

        self.stop_btn = tk.Button(left, text="Stop Recording", width=22, command=self.stop, state="disabled")
        self.stop_btn.pack(pady=6)

        tk.Button(left, text="Play Script", width=22, command=self.play).pack(pady=6)
        tk.Button(left, text="Save Script", width=22, command=self.save).pack(pady=6)
        tk.Button(left, text="Load Script", width=22, command=self.load).pack(pady=6)
        tk.Button(left, text="Clear Script", width=22, command=self.clear).pack(pady=6)

        # Right side: listbox
        right = tk.Frame(root)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Recorded Steps").pack()
        self.listbox = tk.Listbox(right, width=80, height=30)
        self.listbox.pack(fill="both", expand=True)

    def launch(self):
        if self.driver:
            messagebox.showinfo("Browser", "Already launched.")
            return

        try:
            self.driver = get_driver_with_temp_profile()
            self.rec = Recorder(self.driver)
            self.start_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))

    def go(self):
        if not self.driver:
            return
        url = self.url.get().strip()
        self.driver.get(url)
        self.rec.inject()  # inject recorder after navigation

    def start(self):
        self.rec.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.polling = True
        threading.Thread(target=self.ui_updater, daemon=True).start()

    def stop(self):
        self.rec.stop()
        self.polling = False
        self.stop_btn.config(state="disabled")
        self.start_btn.config(state="normal")
        self.update_list()

    def ui_updater(self):
        while self.polling:
            self.update_list()
            time.sleep(0.5)

    def update_list(self):
        script = self.rec.get_script()
        self.listbox.delete(0, tk.END)
        for s in script:
            self.listbox.insert(tk.END, f"{s.get('action')} -> {s.get('selector')}")

    def play(self):
        if not self.rec:
            return
        threading.Thread(target=self.rec.play, daemon=True).start()

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        self.rec.save(path)

    def load(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        self.rec.load(path)
        self.update_list()

    def clear(self):
        self.rec.clear()
        self.update_list()
