# platforms/redbus/bot.py
import time
from selenium.webdriver.common.by import By
from core.base import BotBase
from core.session_manager import SessionManager
from . import locators

class RedBusBot(BotBase):

    def open_site(self):
        self.d.get("https://www.redbus.in")
        time.sleep(2)

    def ensure_login(self):
        if SessionManager.is_logged_in_redbus(self.d):
            print("Already logged in.")
            return

        # Open account → Sign In
        try:
            self.click(*locators.ACCOUNT_MENU)
            time.sleep(1)
            self.click(*locators.LOGIN_OPTION)
        except:
            pass

        print("Please login manually in the browser window.")
        input("Press ENTER here after login is done...")

    def search_buses(self, src, dst, date):
        self.type(*locators.FROM_FIELD, src)
        self.type(*locators.TO_FIELD, dst)

        # Set date
        self.d.execute_script(
            f"document.getElementById('onward_cal').value='{date}'"
        )
        time.sleep(1)

        self.click(*locators.SEARCH_BUTTON)
        time.sleep(5)

    def open_first_bus(self):
        buses = self.find_all(*locators.BUS_CARD)
        if not buses:
            print("No buses found.")
            return

        buses[0].click()
        print("Opened first bus.")
