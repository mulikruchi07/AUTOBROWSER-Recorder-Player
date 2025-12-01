import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BotBase:
    def __init__(self, driver):
        self.d = driver

    def wait(self, by, selector, timeout=20):
        return WebDriverWait(self.d, timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def click(self, by, selector, timeout=20):
        el = WebDriverWait(self.d, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        el.click()
        time.sleep(random.uniform(0.5, 1.1))

    def type(self, by, selector, text):
        el = self.wait(by, selector)
        el.clear()
        el.send_keys(text)
        time.sleep(random.uniform(0.5, 1.1))

    def find_all(self, by, selector):
        try:
            return self.d.find_elements(by, selector)
        except:
            return []
