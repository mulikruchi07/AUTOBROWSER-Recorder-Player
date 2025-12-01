import time
from selenium.webdriver.common.by import By
from core.base import BotBase
from core.session_manager import SessionManager
from ui.login_window import LoginWindow # New import for manual login
from . import locators

class RedBusBot(BotBase):

    def open_site(self):
        self.d.get("https://www.redbus.in")
        time.sleep(2)
        self.close_popups()

    def close_popups(self):
        # close new-user popup
        try:
            close_btns = self.find_all(By.XPATH, "//i[contains(@class,'icon-close') or contains(@class,'close')]")
            for c in close_btns:
                c.click()
                time.sleep(1)
        except:
            pass

    def ensure_login(self):
        if SessionManager.is_logged_in_redbus(self.d):
            print("Already logged in via profile.")
            return True
        else:
            print("User NOT logged in. Attempting login via UI/manual intervention.")

            # Step 1: Open the login modal
            try:
                # Click 'Account' and then 'Sign In'
                self.click(By.XPATH, "//div[text()='Account']")
                time.sleep(1)
                self.click(By.XPATH, locators.LOGIN_BTN) 
            except Exception as e:
                print(f"Could not open login modal: {e}")

            # Step 2: Get credentials from Tkinter UI
            user, pw = LoginWindow().run()
            if not user or not pw:
                print("Login cancelled by user.")
                return False
            
            # --- NOTE ON REDBUS LOGIN ---
            # RedBus typically uses OTP-based login, not a simple password field. 
            # The below logic will enter the mobile/email, but the user must solve the OTP/captcha manually.
            
            # Step 3: Enter the Mobile/Email
            self.type(By.XPATH, locators.MOBILE_FIELD, user) 
            
            # Step 4: Wait for user to complete the login
            # Since full automation for OTP/Captcha is complex, we use a manual pause.
            input("RedBus requires OTP/Manual login after entering mobile number. Please complete login in browser then press ENTER...")
            
            # Check for login status after the manual step
            time.sleep(3)
            return SessionManager.is_logged_in_redbus(self.d)

    def search_buses(self, src, dst, date):
        self.type(By.XPATH, locators.FROM_FIELD, src)
        time.sleep(1)
        self.type(By.XPATH, locators.TO_FIELD, dst)
        time.sleep(1)

        self.click(By.XPATH, locators.DATE_FIELD)
        time.sleep(1)
        # Execute script to force the date value (less robust than clicking the calendar, but fast)
        self.d.execute_script(f"document.getElementById('onward_cal').value='{date}'")

        self.click(By.XPATH, locators.SEARCH_BTN)
        time.sleep(5)

    def open_first_bus(self):
        buses = self.find_all(By.XPATH, locators.FIRST_BUS)
        if not buses:
            print("No buses found.")
            return
        
        # Look for a 'View Seats' or similar button to click the details
        view_seats = self.find_all(By.XPATH, "//div[contains(text(),'View Seats') or contains(text(),'SELECT SEATS')]")
        if view_seats:
            view_seats[0].click()
            print("Clicked 'View Seats' for the first bus.")
        else:
            # Fallback (may just expand the card)
            buses[0].click()
            print("Opened first bus card.")
        time.sleep(3)