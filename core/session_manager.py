# core/session_manager.py
from selenium.webdriver.common.by import By

class SessionManager:
    @staticmethod
    def is_logged_in_redbus(driver):
        try:
            btns = driver.find_elements(
                By.XPATH,
                "//span[contains(text(),'Logout') or contains(text(),'Sign Out')]"
            )
            return len(btns) > 0
        except:
            return False
