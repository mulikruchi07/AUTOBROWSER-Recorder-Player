# platforms/redbus/locators.py
from selenium.webdriver.common.by import By

ACCOUNT_MENU = (By.XPATH, "//div[contains(text(),'Account')]")
LOGIN_OPTION = (By.XPATH, "//div[contains(text(),'Sign In')]")

FROM_FIELD = (By.ID, "src")
TO_FIELD = (By.ID, "dest")
DATE_FIELD = (By.ID, "onward_cal")

SEARCH_BUTTON = (By.XPATH, "//button[contains(text(),'Search')]")

BUS_CARD = (By.XPATH, "//div[contains(@class,'bus-item') or contains(@class,'bus-card')]")
