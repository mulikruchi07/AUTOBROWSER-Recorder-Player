from core.base import BotBase
from core.session_manager import SessionManager
from ui.login_window import LoginWindow
from selenium.webdriver.common.by import By
from . import locators
import time

class ExampleBot(BotBase):
    def __init__(self, driver):
        super().__init__(driver)

    def open_site(self):
        self.d.get("https://github.com/")  # example site URL
    def ensure_login(self):
        if SessionManager.is_logged_in(self.d, "example_site"):
            print("Already logged in via profile.")
            return True

        # ask user for credentials and login
        user, pw = LoginWindow().run()
        if not user or not pw:
            raise Exception("Login cancelled by user.")

        # execute login steps (update locators for real site)
        self.click(By.XPATH, locators.LOGIN_BUTTON)
        self.type(By.XPATH, locators.USERNAME, user)
        self.type(By.XPATH, locators.PASSWORD, pw)
        # user might need to solve captcha — pause for manual step if needed
        input("If captcha appears, solve it in the browser then press Enter to continue...")

        # after login submit: modify if site needs different action
        # self.click(By.XPATH, locators.SUBMIT_BUTTON)

        # wait a bit then check
        time.sleep(3)
        return SessionManager.is_logged_in(self.d, "example_site")

    def search_and_open(self, query):
        self.type(By.XPATH, locators.SEARCH_BOX, query)
        self.click(By.XPATH, locators.SEARCH_BUTTON)
        # wait, parse results, and choose first result — modify selectors to real ones
        time.sleep(2)
        results = self.safe_find_elements(By.XPATH, "//a[contains(@href, '/product') or contains(@class,'product')]")
        if results:
            href = results[0].get_attribute("href")
            self.d.get(href)
            print("Opened product page, stop here for payment.")
        else:
            print("No results found.")
