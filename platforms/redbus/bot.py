import time
from selenium.webdriver.common.by import By
from core.base import BotBase
from core.session_manager import SessionManager
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
            print("Already logged in.")
            return True
        else:
            print("User NOT logged in. Please login manually if popup shows.")

            try:
                self.click(By.XPATH, "//div[text()='Account']")
                time.sleep(2)
                self.click(By.XPATH, "//div[contains(text(),'Sign In')]")
            except:
                pass

            input("Complete login manually in browser, then press ENTER...")
            return True

    def search_buses(self, src, dst, date):
        self.type(By.XPATH, locators.FROM_FIELD, src)
        time.sleep(1)
        self.type(By.XPATH, locators.TO_FIELD, dst)
        time.sleep(1)

        self.click(By.XPATH, locators.DATE_FIELD)
        time.sleep(1)
        self.d.execute_script(f"document.getElementById('onward_cal').value='{date}'")

        self.click(By.XPATH, locators.SEARCH_BTN)
        time.sleep(5)

    def open_first_bus(self):
        buses = self.find_all(By.XPATH, locators.FIRST_BUS)
        if not buses:
            print("No buses found.")
            return
        buses[0].click()
        print("Opened first bus details.")
