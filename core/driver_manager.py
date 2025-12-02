# core/driver_manager.py
import os
import platform
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

def get_chrome_binary_path():
    """
    Detect correct Chrome executable path.
    Adjust manually if needed.
    """
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p

    raise FileNotFoundError(
        "Chrome binary not found. Update get_chrome_binary_path() with the correct location."
    )

def default_chrome_user_data_path():
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
    if system == "Darwin":
        return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
    return os.path.join(home, ".config", "google-chrome")

def get_driver_for_profile(user_data_dir, profile_directory):
    chrome_binary = get_chrome_binary_path()

    options = webdriver.ChromeOptions()
    options.binary_location = chrome_binary

    # REQUIRED FLAGS FOR PROFILE-BASED SELENIUM
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=RendererCodeIntegrity")
    options.add_argument("--disable-background-mode")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")

    # PROFILE
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_directory}")

    # Avoid automation banners
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Driver
    service = Service(ChromeDriverManager().install())

    try:
        driver = webdriver.Chrome(service=service, options=options)
        # hide navigator.webdriver
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        return driver
    except WebDriverException as e:
        raise RuntimeError(
            f"Chrome failed to start with the selected profile.\nFull error:\n{str(e)}"
        )
