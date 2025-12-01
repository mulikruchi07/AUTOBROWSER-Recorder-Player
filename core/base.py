import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

class BotBase:
    def __init__(self, driver):
        self.d = driver

    def wait(self, by, selector, timeout=20):
        """Waits for an element to be present on the DOM."""
        try:
            return WebDriverWait(self.d, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            print(f"Timeout: Element not found using {by.upper()}: {selector}")
            return None

    def click(self, by, selector, timeout=20):
        """Waits for an element to be clickable and clicks it."""
        try:
            el = WebDriverWait(self.d, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            el.click()
            time.sleep(random.uniform(0.5, 1.1)) # Add human-like delay
            return True
        except TimeoutException:
            print(f"Click failed: Element not clickable/visible using {by.upper()}: {selector}")
            return False
        except ElementClickInterceptedException:
            print(f"Click failed: Element intercepted by another element. Using JS click.")
            try:
                el = self.d.find_element(by, selector)
                self.d.execute_script("arguments[0].click();", el)
                time.sleep(random.uniform(0.5, 1.1))
                return True
            except:
                return False


    def type(self, by, selector, text):
        """Waits for an element and types text into it."""
        try:
            el = self.wait(by, selector)
            if el:
                el.clear()
                el.send_keys(text)
                time.sleep(random.uniform(0.5, 1.1))
                return True
            return False
        except NoSuchElementException:
            print(f"Type failed: Element not found using {by.upper()}: {selector}")
            return False

    def find_all(self, by, selector):
        """Returns a list of all matching elements, or an empty list if none found."""
        try:
            return self.d.find_elements(by, selector)
        except:
            return []