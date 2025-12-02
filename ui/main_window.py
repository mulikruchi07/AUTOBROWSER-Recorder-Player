# ui/main_window.py
import tkinter as tk

class MainWindow:
    def run(self):
        root = tk.Tk()
        root.title("CTRL+ALT+TICKET")
        root.geometry("350x180")

        tk.Label(root, text="Select Platform").pack(pady=10)

        val = tk.StringVar(value="redbus")

        tk.Radiobutton(root, text="RedBus", variable=val, value="redbus").pack()

        def start():
            self.choice = val.get()
            root.destroy()

        tk.Button(root, text="Start", command=start).pack(pady=20)

        root.mainloop()
        return getattr(self, "choice", None)
