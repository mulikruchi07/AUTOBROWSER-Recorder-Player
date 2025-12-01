import os
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_driver_using_profile(profile_path):
    """
    Launch Selenium using the selected real Chrome profile path.
    The profile path must point to the 'Default' or 'Profile X' folder
    inside the main User Data directory.
    """
    options = Options()
    options.add_argument("--start-maximized")
    
    # CRITICAL: We pass the *parent* folder path to --user-data-dir
    # and use --profile-directory to specify the exact profile folder.
    # We must extract the actual 'User Data' path and the profile folder name.
    # Example: profile_path is C:\...\User Data\Default
    # data_dir is C:\...\User Data
    # profile_dir is Default
    
    # We assume profile_path is the full path to the profile folder (e.g., C:\...\User Data\Default)
    profile_dir_name = os.path.basename(profile_path)
    user_data_dir = os.path.dirname(profile_path)
    
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_dir_name}")

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
    
    print(f"Driver initialized using Profile Folder: {profile_dir_name}")

    return driver