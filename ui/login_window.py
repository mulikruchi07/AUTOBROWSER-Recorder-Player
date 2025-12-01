import tkinter as tk

class LoginWindow:
    def __init__(self):
        self.username = None
        self.password = None

    def run(self):
        root = tk.Tk()
        root.title("Login Required")
        root.geometry("350x250")
        root.attributes('-topmost', True) # Keep the window on top

        tk.Label(root, text="--- Manual Login Credentials ---", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(root, text="Mobile / Email").pack(pady=5)
        user_e = tk.Entry(root, width=35)
        user_e.pack()

        # NOTE: RedBus uses OTP, so the password field is mainly for other sites or context
        tk.Label(root, text="Password (Optional for RedBus)").pack(pady=5) 
        pass_e = tk.Entry(root, width=35, show="*")
        pass_e.pack()

        def submit():
            self.username = user_e.get()
            self.password = pass_e.get()
            root.destroy()

        tk.Button(root, text="Submit & Continue", command=submit, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=15)
        root.mainloop()
        return self.username, self.password