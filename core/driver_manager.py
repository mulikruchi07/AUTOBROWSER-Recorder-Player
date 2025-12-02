import os
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_driver_using_profile(profile_path):
    """
    Launch Selenium using the selected real Chrome profile path.
    
    profile_path: Full path to the specific profile folder (e.g., C:\...\User Data\Profile 9)
    """
    options = Options()
    options.add_argument("--start-maximized")
    
    # CRITICAL FIX: Ensure correct separation of User Data path and Profile Folder name.
    # profile_path: C:\Users\Rucha\AppData\Local\Google\Chrome\User Data\Profile 9
    
    # 1. Extract the name of the profile folder (e.g., 'Profile 9')
    profile_dir_name = os.path.basename(profile_path)
    
    # 2. Extract the parent 'User Data' directory (e.g., 'C:\Users\Rucha\AppData\Local\Google\Chrome\User Data')
    user_data_dir = os.path.dirname(profile_path)
    
    # Set the arguments required by Chrome
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_dir_name}")

    # Add arguments to help prevent the "Chrome instance exited" error:
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Disable automation flag (stealth mode)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Use a try-except block to provide better feedback on the common error
    try:
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
        
    except Exception as e:
        print("\n------------------------------------------------------------------------------------------------")
        print("CRITICAL ERROR: Failed to create Selenium session.")
        print(f"Error Details: {e}")
        print("\nCommon Causes:")
        print("1. Your Chrome browser is open and using the selected profile. Close all Chrome windows.")
        print("2. Chrome is outdated or corrupted. Try updating or reinstalling Chrome.")
        print("3. There might be a temporary permission issue. Try running the script as Administrator.")
        print("------------------------------------------------------------------------------------------------\n")
        raise # Re-raise the exception to terminate the program properly