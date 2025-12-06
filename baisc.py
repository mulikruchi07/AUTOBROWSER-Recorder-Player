from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://www.example.com")

driver.execute_script("window.XTEST = 123;")
print(driver.execute_script("return window.XTEST;"))

driver.quit()
