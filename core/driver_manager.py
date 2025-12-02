# core/driver_manager.py
import os
import platform
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

def default_chrome_user_data_path():
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local")), "Google", "Chrome", "User Data")
    if system == "Darwin":
        return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
    # Linux
    return os.path.join(home, ".config", "google-chrome")

def get_driver_for_profile(user_data_dir, profile_directory, headless=False, verbose=False):
    """
    Launch Chrome using an existing user-data dir and profile-directory.
    user_data_dir: full path to "User Data" folder (contains Default, Profile 1, ...)
    profile_directory: profile folder name (e.g., "Default", "Profile 1", "CTRL-ALT-PROFILE")
    """
    if not os.path.exists(user_data_dir):
        raise FileNotFoundError(f"user-data-dir not found: {user_data_dir}")

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_directory}")

    # reduce obvious automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    try:
        driver = webdriver.Chrome(service=service, options=options)
        # attempt to hide webdriver property
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception:
            pass
        return driver
    except WebDriverException as e:
        # raise a clearer message for the caller to act on
        raise RuntimeError(f"Failed to create Selenium session. Details: {e}") from e
