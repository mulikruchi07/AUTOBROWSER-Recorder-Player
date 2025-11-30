import tkinter as tk
from tkinter import messagebox

class MainWindow:
    def __init__(self, platforms):
        self.platforms = platforms
        self.selected = None

    def run(self):
        root = tk.Tk()
        root.title("CTRL+ALT+TICKET")
        root.geometry("420x220")

        tk.Label(root, text="Choose platform to run bot for:").pack(pady=(12,0))
        var = tk.StringVar(value=self.platforms[0])
        for p in self.platforms:
            tk.Radiobutton(root, text=p, variable=var, value=p).pack(anchor="w", padx=18)

        tk.Label(root, text="Chrome profile name (optional)").pack(pady=(12,0))
        profile_entry = tk.Entry(root, width=30)
        profile_entry.insert(0, "default")
        profile_entry.pack()

        def start():
            self.selected = var.get()
            self.profile = profile_entry.get().strip() or "default"
            root.destroy()

        tk.Button(root, text="Start Bot", command=start).pack(pady=18)
        root.mainloop()
        return getattr(self, "selected", None), getattr(self, "profile", "default")
