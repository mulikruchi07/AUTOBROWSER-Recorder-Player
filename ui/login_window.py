import tkinter as tk
from tkinter import simpledialog

class LoginWindow:
    def __init__(self, title="Login Required"):
        self.title = title
        self.username = None
        self.password = None

    def run(self):
        root = tk.Tk()
        root.title(self.title)
        root.geometry("350x180")
        root.resizable(False, False)

        tk.Label(root, text="Username / Email").pack(pady=(12, 0))
        username_entry = tk.Entry(root, width=40)
        username_entry.pack()

        tk.Label(root, text="Password").pack(pady=(8, 0))
        password_entry = tk.Entry(root, show="*", width=40)
        password_entry.pack()

        def submit():
            self.username = username_entry.get().strip()
            self.password = password_entry.get().strip()
            root.destroy()

        def cancel():
            root.destroy()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Submit", width=12, command=submit).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", width=12, command=cancel).pack(side="left", padx=6)

        root.mainloop()
        return self.username, self.password
