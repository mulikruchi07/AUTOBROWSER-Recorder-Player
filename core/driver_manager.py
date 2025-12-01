import os
import subprocess
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

def get_chrome_executable():
    """
    Auto-detect Chrome installation.
    Adjust path manually if needed.
    """
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    raise Exception("Chrome executable not found. Update paths manually in get_chrome_executable().")


def get_driver_using_profile(profile_path):
    """
    Launch Selenium using the selected real Chrome profile.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={profile_path}")

    # Disable automation flag (stealth mode)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # Remove navigator.webdriver flag
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )

    return driver
