import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# URL to scrape
url = "https://mtg.fandom.com/wiki/Set"

# Set up the undetected_chromedriver
driver = uc.Chrome()

# Open the webpage
driver.get(url)

# Wait for the specific element that indicates the page has fully loaded
try:
    element_present = EC.presence_of_element_located((By.CLASS_NAME, 'wikitable'))
    WebDriverWait(driver, 10).until(element_present)
except TimeoutException:
    print("Timed out waiting for page to load")
    driver.quit()
    exit()

# Get the page source
page_source = driver.page_source

# Save the page source to an HTML file
with open('page_source.html', 'w', encoding='utf-8') as file:
    file.write(page_source)

# Close the WebDriver
driver.quit()

print("Page source saved to 'page_source.html'")
