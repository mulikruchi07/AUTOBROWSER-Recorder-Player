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
        
        # 1. Read the Local State file
        local_state_file = os.path.join(base_path, "Local State")
        
        if not os.path.exists(local_state_file):
            print(f"Local State file not found at: {local_state_file}")
            return profiles # Return empty if file is missing

        try:
            with open(local_state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # Navigate to the profile info section
            # This path is the most reliable for mapping folder names to display names
            profile_info = state.get('profile', {}).get('info_cache', {})
            
            for folder_name, info in profile_info.items():
                # Check if the folder represents an actual user profile
                if folder_name.startswith("Profile") or folder_name == "Default":
                    full_path = os.path.join(base_path, folder_name)
                    
                    # Ensure the physical profile folder exists
                    if os.path.isdir(full_path):
                        # Use the user-defined name ('name' field)
                        display_name = info.get('name', folder_name) 
                        profiles[display_name] = folder_name
                        
        except Exception as e:
            print(f"Error reading and parsing Chrome Local State file: {e}")
            
        return profiles

    def run(self):
        root = tk.Tk()
        root.title("Choose Chrome Profile")
        root.geometry("420x250")
        root.attributes('-topmost', True)

        tk.Label(root, text="Select Chrome User Profile:").pack(pady=10)

        # Standard Windows path to Chrome User Data
        base_path = os.path.join(
            os.path.expanduser('~'), 
            "AppData", "Local", "Google", "Chrome", "User Data"
        )
        
        if not os.path.exists(base_path):
            # Gracefully handle missing base directory
            messagebox.showerror("Error", f"Chrome User Data folder not found at: {base_path}")
            root.destroy()
            return None # Terminate program gracefully
        
        # Get the mapping of display names to folder names
        profile_map = self._get_chrome_profiles(base_path)
        display_names = list(profile_map.keys())

        if not display_names:
            # Gracefully handle no profiles found (Issue #3 fix)
            messagebox.showerror("Error", "No user-defined Chrome profiles found inside User Data. Please ensure Chrome profiles exist.")
            root.destroy()
            return None # Terminate program gracefully
            
        # UI setup
        profile_box = ttk.Combobox(root, values=display_names, state="readonly", width=40)
        profile_box.pack(pady=10)
        
        # Set default selection (try to select the one named "Default" first)
        default_name_to_select = next((name for name, folder in profile_map.items() if folder == "Default"), display_names[0])
        profile_box.set(default_name_to_select)


        def select():
            chosen_display_name = profile_box.get()
            
            # Use the display name to look up the internal folder name (e.g., 'Profile 9')
            chosen_folder_name = profile_map.get(chosen_display_name)
            
            # The profile_path we return is the full path to the FOLDER 
            self.profile_path = os.path.join(base_path, chosen_folder_name)
            
            root.destroy()

        tk.Button(root, text="Use This Profile", command=select).pack(pady=20)
        root.mainloop()
        
        # Return the full path to the profile folder
        return getattr(self, "profile_path", None)