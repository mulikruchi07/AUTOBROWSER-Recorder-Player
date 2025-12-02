import tkinter as tk

class SearchInputWindow:
    """
    A simple Tkinter UI to collect specific search parameters for RedBus.
    This replaces hardcoded values in main.py.
    """
    def __init__(self):
        self.src = None
        self.dst = None
        self.date = None

    def run(self):
        root = tk.Tk()
        root.title("Enter Trip Details (RedBus)")
        root.geometry("400x300")
        root.attributes('-topmost', True)

        tk.Label(root, text="--- RedBus Search Details ---", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Source (From)
        tk.Label(root, text="Source (e.g., Mumbai)").pack(pady=5)
        src_e = tk.Entry(root, width=40)
        src_e.insert(0, "Mumbai")
        src_e.pack()

        # Destination (To)
        tk.Label(root, text="Destination (e.g., Pune)").pack(pady=5)
        dst_e = tk.Entry(root, width=40)
        dst_e.insert(0, "Pune")
        dst_e.pack()

        # Date
        tk.Label(root, text="Travel Date (e.g., 25-Dec-2025)").pack(pady=5)
        date_e = tk.Entry(root, width=40)
        date_e.insert(0, "25-Dec-2025")
        date_e.pack()

        def submit():
            self.src = src_e.get()
            self.dst = dst_e.get()
            self.date = date_e.get()
            root.destroy()

        tk.Button(root, text="Search Buses", command=submit, bg="#008CBA", fg="white", font=("Arial", 12, "bold")).pack(pady=20)
        root.mainloop()
        
        # Return the collected values
        return self.src, self.dst, self.date