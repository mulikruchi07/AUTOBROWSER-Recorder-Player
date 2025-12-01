from selenium.webdriver.common.by import By

# Login Locators
LOGIN_BTN = "//div[contains(text(),'Sign In')]"
MOBILE_FIELD = "//input[@id='mobileNoInp']"
OTP_BTN = "//button[contains(text(),'GENERATE OTP')]"

# Search Locators
FROM_FIELD = "//input[@id='src']"
TO_FIELD = "//input[@id='dest']"
DATE_FIELD = "//input[@id='onward_cal']"
SEARCH_BTN = "//button[contains(text(),'Search Buses')]"

# Results Locators
FIRST_BUS = "//div[contains(@class,'bus-card')]"
VIEW_SEATS_BTN = "//div[contains(text(),'View Seats')]"
SELECT_SEATS_BTN = "//div[contains(text(),'SELECT SEATS')]"