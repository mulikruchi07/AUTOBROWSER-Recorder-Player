import time
from selenium.webdriver.common.by import By
from core.base import BotBase
from core.session_manager import SessionManager
from ui.login_window import LoginWindow
from . import locators
from selenium.common.exceptions import WebDriverException, TimeoutException

class RedBusBot(BotBase):

    def open_site(self):
        print("Navigating to RedBus...")
        
        # 1. Wait for driver to stabilize after launch
        time.sleep(2) 
        
        try:
            # 2. Attempt navigation
            self.d.get("https://www.redbus.in")
            print("Successfully loaded RedBus.")
        except WebDriverException as e:
            print(f"ERROR: Failed to navigate to RedBus URL. Details: {e}")
            raise # Re-raise to terminate gracefully if navigation fails.

        time.sleep(3) # Wait for page content to load
        self.close_popups()

    def close_popups(self):
        """Attempts to close various popups/modals that block interaction."""
        try:
            # Common close button selectors used on RedBus
            close_btns = self.find_all(By.XPATH, "//i[contains(@class,'icon-close') or contains(@class,'close')]")
            if close_btns:
                for c in close_btns:
                    try:
                        c.click()
                        time.sleep(0.5)
                    except:
                        self.d.execute_script("arguments[0].click();", c)
                        time.sleep(0.5)
                # print(f"Closed {len(close_btns)} potential popups.")
        except Exception:
            # Silently pass errors for optional actions like closing popups
            pass

    def ensure_login(self):
        if SessionManager.is_logged_in_redbus(self.d):
            print("Status: Already logged in via Chrome profile.")
            return True
        else:
            print("Status: User NOT logged in. Initiating manual login process.")

            # Step 1: Open the login modal
            try:
                # Click 'Account' and wait for element to be present
                if not self.click(By.XPATH, "//div[text()='Account']", timeout=10):
                    print("Could not find 'Account' button.")
                    return False
                
                time.sleep(1)
                # Click 'Sign In'
                if not self.click(By.XPATH, locators.LOGIN_BTN, timeout=5):
                    print("Could not find 'Sign In' button.")
                    return False
                time.sleep(2)
            except Exception as e:
                print(f"Could not open login modal: {e}")
                return False

            # Step 2: Get credentials from Tkinter UI
            mobile_or_email, _ = LoginWindow().run() 
            if not mobile_or_email:
                print("Login cancelled by user.")
                return False
            
            # Step 3: Enter the Mobile/Email
            if not self.type(By.XPATH, locators.MOBILE_FIELD, mobile_or_email):
                print("Failed to enter mobile number/email. Element missing.")
                return False
            
            # Step 4: Click the OTP button
            if not self.click(By.XPATH, locators.OTP_BTN):
                print("Failed to click 'GENERATE OTP'. Element missing or intercepted.")
                return False

            # Step 5: Wait for user to complete the login manually (OTP/Captcha)
            print("--- MANUAL INTERVENTION REQUIRED ---")
            print("RedBus requires OTP/Manual login after entering mobile number.")
            input("Please complete login in the browser now (solve OTP/Captcha), then press ENTER to continue script...")
            print("------------------------------------")
            
            # Check for login status after the manual step
            time.sleep(5)
            if SessionManager.is_logged_in_redbus(self.d):
                print("Login successful (verified after manual step).")
                return True
            else:
                print("Login failed or could not be verified.")
                return False


    def search_buses(self, src, dst, date):
        print(f"Searching for: {src} to {dst} on {date}...")
        
        # Locate the Source field and type. Must click first to activate the input
        if not self.click(By.XPATH, locators.FROM_FIELD, timeout=10): return
        if not self.type(By.XPATH, locators.FROM_FIELD, src): return
        time.sleep(1.5) # Wait for autocomplete list to appear (RedBus standard)
        
        # Locate the Destination field and type
        if not self.click(By.XPATH, locators.TO_FIELD): return
        if not self.type(By.XPATH, locators.TO_FIELD, dst): return
        time.sleep(1.5)
        
        # Handle Date Picker - opening the calendar
        if not self.click(By.XPATH, locators.DATE_FIELD): return
        time.sleep(1)
        
        # Use JS to force the date value, as this bypasses calendar interaction complexity
        self.d.execute_script(f"document.getElementById('onward_cal').value='{date}';")
        print("Date set via JavaScript.")

        # Click the Search button
        if not self.click(By.XPATH, locators.SEARCH_BTN): return
        print("Search button clicked. Waiting for results...")
        time.sleep(10) # Extended wait for search results page load

    def open_first_bus(self):
        print("Attempting to open the first bus details...")
        
        # 1. Try to find the 'View Seats' button on the first result
        # We use wait() here to ensure the element is loaded after the search
        view_seats_btn = self.wait(By.XPATH, "//div[contains(text(),'View Seats')]", timeout=15)
        
        if view_seats_btn:
            print("Clicking 'View Seats' for the first result...")
            self.d.execute_script("arguments[0].scrollIntoView(true);", view_seats_btn)
            view_seats_btn.click()
            time.sleep(5)
            return
        
        print("No 'View Seats' button found after search. Stopping flow.")
        return