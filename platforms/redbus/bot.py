import time
from selenium.webdriver.common.by import By
from core.base import BotBase
from core.session_manager import SessionManager
from ui.login_window import LoginWindow
from . import locators

class RedBusBot(BotBase):

    def open_site(self):
        print("Navigating to RedBus...")
        self.d.get("https://www.redbus.in")
        time.sleep(3)
        self.close_popups()

    def close_popups(self):
        """Attempts to close various popups/modals that block interaction."""
        try:
            # Common close button selectors used on RedBus
            close_btns = self.find_all(By.XPATH, "//i[contains(@class,'icon-close') or contains(@class,'close')]")
            for c in close_btns:
                try:
                    c.click()
                    time.sleep(0.5)
                except:
                    # Use JavaScript click if regular click fails (e.g., element still transitioning)
                    self.d.execute_script("arguments[0].click();", c)
                    time.sleep(0.5)
            if close_btns:
                print(f"Closed {len(close_btns)} potential popups.")
        except Exception as e:
            print(f"Error during popup handling: {e}")
            pass

    def ensure_login(self):
        if SessionManager.is_logged_in_redbus(self.d):
            print("Status: Already logged in via Chrome profile.")
            return True
        else:
            print("Status: User NOT logged in. Initiating manual login process.")

            # Step 1: Open the login modal
            try:
                # Click 'Account'
                if not self.click(By.XPATH, "//div[text()='Account']", timeout=5):
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
            # We assume user provides mobile number/email in the UI
            mobile_or_email, _ = LoginWindow().run() 
            if not mobile_or_email:
                print("Login cancelled by user.")
                return False
            
            # Step 3: Enter the Mobile/Email
            if not self.type(By.XPATH, locators.MOBILE_FIELD, mobile_or_email):
                print("Failed to enter mobile number/email.")
                return False
            
            # Step 4: Click the OTP button
            if not self.click(By.XPATH, locators.OTP_BTN):
                print("Failed to click 'GENERATE OTP'.")
                return False

            # Step 5: Wait for user to complete the login manually (OTP/Captcha)
            print("--- MANUAL INTERVENTION REQUIRED ---")
            print("RedBus requires OTP/Manual login after entering mobile number.")
            input("Please complete login in the browser now (solve OTP/Captcha), then press ENTER to continue script...")
            print("------------------------------------")
            
            # Check for login status after the manual step
            time.sleep(3)
            if SessionManager.is_logged_in_redbus(self.d):
                print("Login successful (verified after manual step).")
                return True
            else:
                print("Login failed or could not be verified.")
                return False


    def search_buses(self, src, dst, date):
        print(f"Searching for: {src} to {dst} on {date}...")
        if not self.type(By.XPATH, locators.FROM_FIELD, src): return
        time.sleep(1)
        if not self.type(By.XPATH, locators.TO_FIELD, dst): return
        time.sleep(1)

        # Handle Date Picker - opening the calendar
        if not self.click(By.XPATH, locators.DATE_FIELD): return
        time.sleep(1)
        
        # NOTE: Clicking through the calendar UI is more robust, but using JS is faster 
        # and avoids complicated date picker logic for a simple automation task.
        self.d.execute_script(f"document.getElementById('onward_cal').value='{date}';")
        print("Date set via JavaScript. You may need to click 'Search' manually if the input field validation prevents submission.")

        if not self.click(By.XPATH, locators.SEARCH_BTN): return
        time.sleep(7) # Wait longer for search results to load

    def open_first_bus(self):
        # The main goal here is to get to the seat selection screen
        
        # 1. Try to find the 'View Seats' button on the first result
        view_seats_btn = self.find_all(By.XPATH, "//div[contains(text(),'View Seats')]")
        if view_seats_btn:
            print("Clicking 'View Seats' for the first result...")
            view_seats_btn[0].click()
            time.sleep(3)
            return
        
        # 2. Fallback: Click the whole bus card if the button wasn't immediately found
        buses = self.find_all(By.XPATH, locators.FIRST_BUS)
        if buses:
            print("Clicking the first bus card to reveal details/seats...")
            buses[0].click()
            time.sleep(3)
            
            # After clicking the card, the 'View Seats' button might appear
            final_select = self.find_all(By.XPATH, "//div[contains(text(),'SELECT SEATS')]")
            if final_select:
                 final_select[0].click()
                 print("Clicked 'SELECT SEATS' after expanding card.")
                 time.sleep(3)
                 return
            
            print("No specific seat selection button found after expanding card. Stopping here.")
            return

        print("No buses found to select.")