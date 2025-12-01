from selenium.webdriver.common.by import By

class SessionManager:
    @staticmethod
    def is_logged_in_redbus(driver):
        try:
            # Check if "My Account" menu indicates user is logged in
            menu = driver.find_elements(By.XPATH, "//span[contains(text(),'Logout') or contains(text(),'Sign Out')]")
            return len(menu) > 0
        except:
            return False
