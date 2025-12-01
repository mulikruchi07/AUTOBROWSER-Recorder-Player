import tkinter as tk

class MainWindow:
    def run(self):
        root = tk.Tk()
        root.title("CTRL+ALT+TICKET")
        root.geometry("380x200")

        tk.Label(root, text="RedBus Bot Automation", font=("Arial", 14)).pack(pady=20)

        val = tk.StringVar(value="redbus")

        tk.Radiobutton(root, text="RedBus", variable=val, value="redbus").pack()

        def start():
            self.chosen = val.get()
            root.destroy()

        tk.Button(root, text="Start Bot", command=start).pack(pady=20)
        root.mainloop()

        return getattr(self, "chosen", None)
