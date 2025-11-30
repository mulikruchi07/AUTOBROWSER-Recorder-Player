from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, random

class BotBase:
    def __init__(self, driver, wait_timeout=20):
        self.d = driver
        self.wait_timeout = wait_timeout

    def wait_for(self, by, selector, clickable=False, timeout=None):
        t = timeout or self.wait_timeout
        if clickable:
            return WebDriverWait(self.d, t).until(EC.element_to_be_clickable((by, selector)))
        return WebDriverWait(self.d, t).until(EC.presence_of_element_located((by, selector)))

    def click(self, by, selector):
        el = self.wait_for(by, selector, clickable=True)
        el.click()
        self._human_wait()

    def type(self, by, selector, text):
        el = self.wait_for(by, selector)
        el.clear()
        el.send_keys(text)
        self._human_wait()

    def extract_text(self, by, selector):
        el = self.wait_for(by, selector)
        return el.text

    def safe_find_elements(self, by, selector):
        try:
            return self.d.find_elements(by, selector)
        except:
            return []

    def _human_wait(self):
        # small random delay to mimic human
        time.sleep(random.uniform(0.6, 1.3))
