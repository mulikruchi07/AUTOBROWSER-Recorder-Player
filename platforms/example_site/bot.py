from core.base import BotBase
from ui.login_window import LoginWindow
from selenium.webdriver.common.by import By
from . import locators
import time

class ExampleSiteBot(BotBase):
    def __init__(self, driver):
        super().__init__(driver)
    
    # Simple check for the placeholder site (e.g., check for a common login link absence)
    def _is_logged_in(self):
        # On GitHub (our example), check if the 'Sign In' or 'Sign Up' button is absent
        login_links = self.find_all(By.XPATH, "//a[contains(@href, '/login') or contains(@href, '/join')]")
        return len(login_links) == 0

    def open_site(self):
        self.d.get("https://github.com/")  # example site URL
        
    def ensure_login(self):
        if self._is_logged_in():
            print("Already logged in via profile.")
            return True

        print("Not logged in. Asking for credentials.")
        user, pw = LoginWindow().run()
        if not user or not pw:
            print("Login cancelled by user.")
            return False
        
        # --- EXECUTE LOGIN STEPS (These are placeholders for a real site) ---
        print("Executing placeholder login steps...")
        self.click(By.XPATH, locators.LOGIN_BUTTON)
        self.type(By.XPATH, locators.USERNAME, user)
        self.type(By.XPATH, locators.PASSWORD, pw)
        
        # User MUST solve any captcha/2FA manually
        input("If captcha/2FA appears, solve it in the browser then press Enter to continue...")

        # wait a bit then check
        time.sleep(5)
        if self._is_logged_in():
            print("Login successful (verified after manual step).")
            return True
        else:
            print("Login failed or could not be verified.")
            return False

    def search_and_open(self, query):
        print(f"Searching for: {query}")
        if not self.type(By.XPATH, locators.SEARCH_BOX, query): return
        if not self.click(By.XPATH, locators.SEARCH_BUTTON): return
        
        # wait, parse results, and choose first result — modify selectors to real ones
        time.sleep(5)
        # Attempt to find the first link in the search results
        first_result = self.find_all(By.XPATH, "//a[contains(@class,'Link--primary')]")
        
        if first_result:
            href = first_result[0].get_attribute("href")
            print(f"Opening first result: {href}")
            self.d.get(href)
            print("Opened the first search result.")
        else:
            print("No search results found.")