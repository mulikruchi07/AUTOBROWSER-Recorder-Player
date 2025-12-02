# ui/login_window.py
import tkinter as tk

class LoginWindow:
    """
    Simple modal that asks for username/password if required.
    For RedBus OTP or Google sign-in flows it's normal to let the user login manually.
    """
    def __init__(self, title="Login Required"):
        self.title = title
        self.username = None
        self.password = None

    def run(self):
        root = tk.Tk()
        root.title(self.title)
        root.geometry("360x200")
        root.resizable(False, False)

        tk.Label(root, text="Mobile / Email").pack(pady=6)
        user_e = tk.Entry(root, width=45)
        user_e.pack()

        tk.Label(root, text="Password (if applicable)").pack(pady=6)
        pass_e = tk.Entry(root, show="*", width=45)
        pass_e.pack()

        def submit():
            self.username = user_e.get().strip()
            self.password = pass_e.get().strip()
            root.destroy()

        tk.Button(root, text="Submit", command=submit).pack(pady=12)
        root.mainloop()
        return self.username, self.password
