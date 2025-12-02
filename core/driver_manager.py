import os
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

def get_driver_using_profile(profile_path):
    r"""
    Launch Selenium using the selected real Chrome profile path automatically.
    
    profile_path: Full path to the specific profile folder (e.g., C:\...\User Data\Profile 9)
    """
    options = Options()
    options.add_argument("--start-maximized")
    
    # 1. Extract the name of the profile folder (e.g., 'Profile 10')
    profile_dir_name = os.path.basename(profile_path)
    
    # 2. Extract the parent 'User Data' directory
    user_data_dir = os.path.dirname(profile_path)
    
    # Set the arguments required by Chrome
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_dir_name}")

    # --- ENHANCED STABILITY OPTIONS (Reverted to Automatic Launch + Critical Fixes) ---
    
    # This specific flag sometimes bypasses profile lock issues that cause "Chrome instance exited"
    options.add_argument("--user-data-dir-compatibility-mode") 
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") 
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    
    # Remove automation flag (stealth mode)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Use a try-except block to provide better feedback on the common error
    try:
        # Use ChromeDriverManager to automatically handle the correct ChromeDriver version
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        # Remove navigator.webdriver flag
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        
        print(f"Driver initialized successfully with Profile: {profile_dir_name}")
        return driver
        
    except WebDriverException as e:
        print("\n------------------------------------------------------------------------------------------------")
        print("CRITICAL ERROR: Failed to create Selenium session.")
        print(f"Error Details: {e}")
        print("\nCOMMON RESOLUTION STEPS (Check these carefully, as the error is external to the code):")
        print("1. **CLOSE CHROME:** Ensure all open Chrome windows and background processes are closed.")
        print("2. **CHECK VERSION:** Ensure your Chrome browser is fully up-to-date.")
        print("3. **RETRY:** Sometimes restarting your PC can clear temporary locks on the profile.")
        print("4. **PERMISSIONS:** Try running your terminal/IDE as Administrator.")
        print("------------------------------------------------------------------------------------------------\n")
        raise # Re-raise the exception to terminate the program properly