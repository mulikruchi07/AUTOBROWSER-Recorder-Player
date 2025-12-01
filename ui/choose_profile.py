import os
import tkinter as tk
from tkinter import ttk, messagebox

class ChromeProfileChooser:
    def __init__(self):
        self.profile_path = None

    def run(self):
        root = tk.Tk()
        root.title("Choose Chrome Profile")
        root.geometry("420x250")

        tk.Label(root, text="Select Chrome User Profile:").pack(pady=10)

        base_path = r"C:\Users\{}\AppData\Local\Google\Chrome\User Data".format(
            os.getlogin()
        )
        if not os.path.exists(base_path):
            messagebox.showerror("Error", "Chrome User Data folder not found.")
            root.destroy()
            return None

        profiles = []
        for folder in os.listdir(base_path):
            full = os.path.join(base_path, folder)
            if os.path.isdir(full):
                profiles.append(folder)

        profile_box = ttk.Combobox(root, values=profiles, state="readonly", width=40)
        profile_box.pack(pady=10)
        profile_box.set("Default" if "Default" in profiles else profiles[0])

        def select():
            chosen = profile_box.get()
            self.profile_path = os.path.join(base_path, chosen)
            root.destroy()

        tk.Button(root, text="Use This Profile", command=select).pack(pady=20)
        root.mainloop()
        return self.profile_path
