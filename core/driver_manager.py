# core/driver_manager.py
import tempfile
import shutil
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_temp_profile_dir():
    """
    Creates a new temporary Chrome user profile directory on each run.
    """
    temp_dir = tempfile.mkdtemp(prefix="ctrl-alt-ticket-profile-")
    return temp_dir

def get_driver_with_temp_profile():
    """
    Launch Chrome with a fresh, isolated temporary profile each time.
    No conflicts, no DevToolsActivePort errors.
    """
    profile_dir = get_temp_profile_dir()

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={profile_dir}")

    # stability flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    # avoid automation banners
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # remove webdriver fingerprinting
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
    except:
        pass

    return driver
