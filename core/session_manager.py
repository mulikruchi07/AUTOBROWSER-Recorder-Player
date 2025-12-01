from selenium.webdriver.common.by import By

class SessionManager:
    @staticmethod
    def is_logged_in_redbus(driver):
        """
        Checks if the user appears to be logged in on RedBus by looking for 
        an indicator like a 'Logout' or 'Sign Out' link.
        """
        try:
            # Check for the presence of elements that only appear post-login
            # RedBus uses 'Account' and usually shows a 'Sign Out' option under the menu
            menu_indicator = driver.find_elements(By.XPATH, "//div[contains(text(),'Sign Out') or contains(text(),'Logout')]")
            # Also check for profile name/icon presence
            profile_name = driver.find_elements(By.XPATH, "//div[contains(@class,'name-row')]")
            
            return len(menu_indicator) > 0 or len(profile_name) > 0
        except:
            return False