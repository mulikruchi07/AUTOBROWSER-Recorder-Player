from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import platform

def default_profile_path():
    # choose cross-platform default folder under project
    base = os.path.abspath(os.path.join(os.getcwd(), "selenium_profiles"))
    os.makedirs(base, exist_ok=True)
    return base

def get_chrome_options(use_profile=True, profile_name="default", headless=False):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    # recommended tweaks to behave more human-like
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)

    if use_profile:
        profile_dir = r"C:\Users\dell\AppData\Local\Google\Chrome\User Data\Default"
        # On first run Chrome creates the profile folder and stores cookies/sessions
        opts.add_argument(f"--user-data-dir={profile_dir}")

    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")

    return opts

def get_driver(use_profile=True, profile_name="default", headless=False):
    opts = get_chrome_options(use_profile=use_profile, profile_name=profile_name, headless=headless)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    # small stealth settings
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
        """
    })
    return driver
