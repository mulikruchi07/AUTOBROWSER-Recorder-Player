import tkinter as tk

class LoginWindow:
    def __init__(self):
        self.username = None
        self.password = None

    def run(self):
        root = tk.Tk()
        root.title("Login Required")
        root.geometry("350x200")

        tk.Label(root, text="Mobile / Email").pack(pady=5)
        user_e = tk.Entry(root, width=35)
        user_e.pack()

        tk.Label(root, text="Password").pack(pady=5)
        pass_e = tk.Entry(root, width=35, show="*")
        pass_e.pack()

        def submit():
            self.username = user_e.get()
            self.password = pass_e.get()
            root.destroy()

        tk.Button(root, text="Submit", command=submit).pack(pady=15)
        root.mainloop()
        return self.username, self.password
