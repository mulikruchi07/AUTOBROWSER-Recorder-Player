from selenium.webdriver.common.by import By

class SessionManager:
    @staticmethod
    def is_logged_in(driver, platform):
        # platform-specific checks
        try:
            if platform == "example_site":
                # change to the real locator for the platform's "account / logout" element
                # Example: check for an element visible only when logged in
                logout_xpath = "//a[contains(., 'Logout') or contains(., 'Sign Out')]"
                els = driver.find_elements(By.XPATH, logout_xpath)
                return len(els) > 0

            # fallback false
            return False
        except Exception:
            return False
