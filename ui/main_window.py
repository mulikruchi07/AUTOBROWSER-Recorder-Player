import tkinter as tk

class MainWindow:
    def run(self):
        root = tk.Tk()
        root.title("CTRL+ALT+TICKET")
        root.geometry("380x250") # Increased height for more options

        tk.Label(root, text="Bot Automation Platform Selector", font=("Arial", 14)).pack(pady=20)

        # Use a list of supported platforms
        platforms = [("RedBus", "redbus"), ("Example Site (GitHub)", "example_site")]
        
        val = tk.StringVar(value=platforms[0][1])

        for text, value in platforms:
            tk.Radiobutton(root, text=text, variable=val, value=value).pack(anchor="w", padx=100)

        def start():
            self.chosen = val.get()
            root.destroy()

        tk.Button(root, text="Start Bot", command=start).pack(pady=20)
        root.mainloop()

        return getattr(self, "chosen", None)