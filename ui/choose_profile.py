# ui/choose_profile.py
import os
import platform
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.driver_manager import default_chrome_user_data_path
import subprocess
import sys

def _is_chrome_running_windows():
    # uses tasklist to detect chrome.exe
    try:
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq chrome.exe"], text=True, stderr=subprocess.DEVNULL)
        return "chrome.exe" in out.lower()
    except Exception:
        return False

def _is_chrome_running_unix():
    try:
        p = subprocess.Popen(["pgrep", "chrome"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        out, _ = p.communicate(timeout=1)
        return bool(out.strip())
    except Exception:
        return False

def is_chrome_running():
    system = platform.system()
    if system == "Windows":
        return _is_chrome_running_windows()
    else:
        return _is_chrome_running_unix()

class ChromeProfileChooser:
    """
    Presents a small dialog:
     - Detects default Chrome User Data path
     - Lists available profile directories (Default, Profile 1, ...)
     - Blocks selection of 'Default' (recommended), encourages creating/choosing another profile
     - Detects if Chrome is running and asks user to close it (or offers to kill processes)
    """
    def __init__(self):
        self.user_data_dir = None
        self.profile = None
        self.forced_profile_warning = "Using 'Default' profile is risky — it is often locked by the system. Prefer a secondary profile."

    def _detect_profiles(self, user_data_dir):
        profiles = []
        if not os.path.exists(user_data_dir):
            return profiles
        for name in os.listdir(user_data_dir):
            path = os.path.join(user_data_dir, name)
            if os.path.isdir(path):
                profiles.append(name)
        profiles.sort()
        return profiles

    def _offer_kill_chrome(self):
        # ask user to kill Chrome processes (Windows only)
        res = messagebox.askyesno("Chrome running", "Chrome processes appear to be running and may lock the profile.\nDo you want the program to terminate all Chrome processes now? (You will lose unsaved tabs.)")
        if not res:
            return False

        system = platform.system()
        try:
            if system == "Windows":
                subprocess.check_call(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # POSIX use pkill -f chrome
                subprocess.check_call(["pkill", "-f", "chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            messagebox.showwarning("Kill failed", f"Could not kill Chrome processes automatically: {e}\nPlease close Chrome manually and try again.")
            return False

    def run(self):
        root = tk.Tk()
        root.title("Choose Chrome Profile")
        root.geometry("620x340")
        root.resizable(False, False)

        tk.Label(root, text="Chrome User Data folder:").pack(anchor="w", padx=12, pady=(12,0))
        default_path = default_chrome_user_data_path()
        path_var = tk.StringVar(value=default_path)
        entry = tk.Entry(root, textvariable=path_var, width=92)
        entry.pack(padx=12, pady=6)

        profiles = self._detect_profiles(default_path)
        tk.Label(root, text="Detected profiles:").pack(anchor="w", padx=12, pady=(8,0))
        profile_box = ttk.Combobox(root, values=profiles, state="readonly", width=48)
        if "Default" in profiles:
            # preselect but show explicit warning; user must confirm if they choose it
            profile_box.set("Default")
        elif profiles:
            profile_box.set(profiles[0])
        profile_box.pack(padx=12, pady=6)

        note = tk.Label(root, text="Note: Avoid using 'Default'. Create a new profile in Chrome (Manage Profiles) named 'CTRL-ALT-PROFILE' if possible.", fg="darkorange")
        note.pack(anchor="w", padx=12, pady=(6,0))

        def refresh():
            p = path_var.get().strip()
            profs = self._detect_profiles(p)
            profile_box['values'] = profs
            if profs:
                profile_box.set(profs[0])
            else:
                profile_box.set("")

        def choose_custom():
            p = simpledialog.askstring("Custom path", "Paste Chrome 'User Data' folder path (exact):")
            if p:
                path_var.set(p)
                refresh()

        def select():
            p = path_var.get().strip()
            prof = profile_box.get().strip()
            if not os.path.exists(p):
                messagebox.showerror("Error", f"User Data path not found:\n{p}")
                return
            if not prof:
                messagebox.showerror("Error", "No profile selected.")
                return

            # Warn and block 'Default' by default
            if prof.lower() == "default":
                ok = messagebox.askyesno("Default profile chosen", "You selected the 'Default' profile which is risky and often locked by Chrome. Proceed anyway?")
                if not ok:
                    return

            # If Chrome is running, ask to close or kill
            if is_chrome_running():
                should_kill = messagebox.askyesno("Chrome running", "Chrome appears to be running. It must be fully closed to let Selenium attach to the profile.\nWould you like the program to attempt to close Chrome processes automatically?")
                if should_kill:
                    killed = self._offer_kill_chrome()
                    if not killed:
                        # bail out so user can close manually
                        messagebox.showinfo("Please close Chrome", "Please close all Chrome windows and background processes, then re-run profile selection.")
                        return
                else:
                    messagebox.showinfo("Please close Chrome", "Please close all Chrome windows and background processes, then re-run profile selection.")
                    return

            self.user_data_dir = p
            self.profile = prof
            root.destroy()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=14)
        tk.Button(btn_frame, text="Refresh", command=refresh, width=12).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Paste custom path", command=choose_custom, width=16).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Use Selected Profile", command=select, width=18).pack(side="left", padx=6)

        root.mainloop()
        return self.user_data_dir, self.profile
