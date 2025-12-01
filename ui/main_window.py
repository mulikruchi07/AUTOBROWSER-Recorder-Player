import tkinter as tk

class MainWindow:
    def run(self):
        root = tk.Tk()
        root.title("CTRL+ALT+TICKET")
        root.geometry("380x250")

        tk.Label(root, text="Bot Automation Platform Selector", font=("Arial", 14, "bold")).pack(pady=20)

        # List of supported platforms (name, internal_key)
        platforms = [
            ("RedBus (Bus Tickets)", "redbus"), 
            ("Example Site (GitHub)", "example_site")
        ]
        
        val = tk.StringVar(value=platforms[0][1])

        for text, value in platforms:
            # Adjusted styling for better UI
            tk.Radiobutton(root, text=text, variable=val, value=value, font=("Arial", 10)).pack(anchor="w", padx=100)

        def start():
            self.chosen = val.get()
            root.destroy()

        tk.Button(root, text="Start Bot", command=start, bg="#008CBA", fg="white", font=("Arial", 12, "bold")).pack(pady=20)
        root.mainloop()

        return getattr(self, "chosen", None)