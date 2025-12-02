# core/base.py
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BotBase:
    def __init__(self, driver):
        self.d = driver

    def wait_presence(self, by, selector, timeout=15):
        return WebDriverWait(self.d, timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def wait_clickable(self, by, selector, timeout=15):
        return WebDriverWait(self.d, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )

    def click(self, by, selector):
        el = self.wait_clickable(by, selector)
        el.click()
        self._human_pause()

    def type(self, by, selector, text):
        el = self.wait_presence(by, selector)
        el.clear()
        el.send_keys(text)
        self._human_pause()

    def find_all(self, by, selector):
        try:
            return self.d.find_elements(by, selector)
        except:
            return []

    def _human_pause(self):
        time.sleep(random.uniform(0.4, 1.2))
