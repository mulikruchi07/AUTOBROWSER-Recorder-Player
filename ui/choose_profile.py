import os
import tkinter as tk
from tkinter import ttk, messagebox
import json

class ChromeProfileChooser:
    def __init__(self):
        self.profile_folder = None

    def _get_chrome_profiles(self, base_path):
        """
        Reads the Chrome User Data directory and extracts human-readable profile names.
        """
        profiles = {}
        
        # Look for folders that represent actual profiles
        for folder_name in os.listdir(base_path):
            if folder_name.startswith("Profile") or folder_name == "Default":
                full_path = os.path.join(base_path, folder_name)
                if os.path.isdir(full_path):
                    
                    # Try to read the human-readable name from the Preferences file
                    prefs_file = os.path.join(full_path, "Preferences")
                    display_name = folder_name # Default to folder name if reading fails
                    
                    try:
                        with open(prefs_file, 'r', encoding='utf-8') as f:
                            prefs = json.load(f)
                            # The human-readable name is often stored under 'profile.name'
                            if 'profile' in prefs and 'name' in prefs['profile']:
                                display_name = prefs['profile']['name']
                    except:
                        # File not found or couldn't parse JSON, use the folder name
                        pass

                    # Store mapping: {Display Name: Folder Name}
                    profiles[display_name] = folder_name
        
        return profiles

    def run(self):
        root = tk.Tk()
        root.title("Choose Chrome Profile")
        root.geometry("420x250")

        tk.Label(root, text="Select Chrome User Profile:").pack(pady=10)

        # Standard Windows path to Chrome User Data
        # Using os.path.join is safer than f-strings with backslashes
        base_path = os.path.join(
            os.path.expanduser('~'), 
            "AppData", "Local", "Google", "Chrome", "User Data"
        )
        
        if not os.path.exists(base_path):
            messagebox.showerror("Error", f"Chrome User Data folder not found at: {base_path}")
            root.destroy()
            return None

        # Get the mapping of display names to folder names
        profile_map = self._get_chrome_profiles(base_path)
        display_names = list(profile_map.keys())

        if not display_names:
            messagebox.showerror("Error", "No Chrome profiles found inside User Data.")
            root.destroy()
            return None
            
        # UI setup
        profile_box = ttk.Combobox(root, values=display_names, state="readonly", width=40)
        profile_box.pack(pady=10)
        
        # Set default selection
        default_name = "Default"
        if "Default" in profile_map:
            profile_box.set(default_name)
        elif display_names:
            profile_box.set(display_names[0])


        def select():
            chosen_display_name = profile_box.get()
            
            # Use the display name to look up the internal folder name
            chosen_folder_name = profile_map.get(chosen_display_name)
            
            # Set the full path to the folder
            self.profile_path = os.path.join(base_path, chosen_folder_name)
            
            root.destroy()

        tk.Button(root, text="Use This Profile", command=select).pack(pady=20)
        root.mainloop()
        
        return getattr(self, "profile_path", None)