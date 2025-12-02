import os
import tkinter as tk
from tkinter import ttk, messagebox
import json

class ChromeProfileChooser:
    def __init__(self):
        self.profile_path = None

    def _get_chrome_profiles(self, base_path):
        """
        Reads the Chrome User Data directory and extracts human-readable profile names 
        from the Local State file, which is the most reliable source for the profile map.
        
        Returns: 
            A dictionary mapping {Display Name: Folder Name (e.g., 'Profile 1')}
        """
        profiles = {}
        
        # 1. Read the Local State file, which holds the official profile mapping
        local_state_file = os.path.join(base_path, "Local State")
        
        if not os.path.exists(local_state_file):
            return profiles # Return empty if file is missing

        try:
            with open(local_state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # Navigate to the profile info section
            gaia_info = state.get('profile', {}).get('gaia_profile_info', {})
            label_map = state.get('profile', {}).get('profile_with_filename_migration', {})
            
            # Use the newer, more descriptive map if available (Display Name -> Folder Name)
            if label_map:
                for folder_name, display_name in label_map.items():
                    # We check if the folder actually exists on disk before adding it
                    full_path = os.path.join(base_path, folder_name)
                    if os.path.isdir(full_path):
                        profiles[display_name] = folder_name
                return profiles

            # Fallback: Use the GAIA info (less reliable for custom names)
            for folder_name, info in gaia_info.items():
                full_path = os.path.join(base_path, folder_name)
                if os.path.isdir(full_path):
                    # Use the name set by the user or the folder name as fallback
                    display_name = info.get('name', folder_name) 
                    profiles[display_name] = folder_name

        except Exception as e:
            print(f"Error reading Chrome Local State file: {e}")
            
        return profiles

    def run(self):
        root = tk.Tk()
        root.title("Choose Chrome Profile")
        root.geometry("420x250")
        root.attributes('-topmost', True) # Keep the window on top

        tk.Label(root, text="Select Chrome User Profile:").pack(pady=10)

        # Standard Windows path to Chrome User Data
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
        if "Default" in profile_map:
            profile_box.set("Default")
        elif display_names:
            # Try to select the first one if Default isn't an option
            profile_box.set(display_names[0])


        def select():
            chosen_display_name = profile_box.get()
            
            # Use the display name to look up the internal folder name (e.g., 'Profile 9')
            chosen_folder_name = profile_map.get(chosen_display_name)
            
            # The profile_path we return is the full path to the FOLDER (e.g., C:\...\User Data\Profile 9)
            self.profile_path = os.path.join(base_path, chosen_folder_name)
            
            root.destroy()

        tk.Button(root, text="Use This Profile", command=select).pack(pady=20)
        root.mainloop()
        
        # Return the full path to the profile folder
        return getattr(self, "profile_path", None)