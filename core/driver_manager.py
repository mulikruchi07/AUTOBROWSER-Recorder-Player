# core/driver_manager.py
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_temp_profile_dir():
    """
    Create a new temporary profile directory to avoid profile lock issues.
    """
    temp_dir = tempfile.mkdtemp(prefix="autobrowser-profile-")
    return temp_dir

def get_driver_with_temp_profile():
    """
    Create and return a Selenium Chrome WebDriver using a fresh temporary profile.
    """
    profile_dir = get_temp_profile_dir()
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={profile_dir}")

    # stability flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception:
        pass

    return driver
