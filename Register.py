import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
# Specify your deadline time here (year, month, day, hour, minute)
deadline = datetime.datetime(2023, 11, 17, 8, 00)  # Example: Nov 17, 2023, at 15:00

# WebDriver path and URL setup
driver_path = 'C:/Program Files/Mozilla Firefox/firefox.exe'
url = 'https://colleague-ss.uoguelph.ca/Student/Planning/DegreePlans'  # Replace with the URL of your login page

# Function to synchronize sleep to the next interval of 10 seconds
def sync_sleep(interval):
    now = datetime.datetime.now()
    sleep_time = interval - (now.second % interval)
    time.sleep(sleep_time)

# Start a browser session
browser = webdriver.Firefox()
browser.get(url)

# Manual login
print("Please log in manually in the browser window.")
print("Input anything into console once logged in.")
input()
print("Starting loop...")
# Calculate the start time (2 minutes before the deadline)
start_time = deadline - datetime.timedelta(minutes=2000000)

# Wait until the start time is reached
while datetime.datetime.now() < start_time:
    sync_sleep(10)  # Check every 10 seconds

# Main process - starts 2 minutes before the deadline
while datetime.datetime.now() < deadline:
    try:
        # If there exists any pre-existing notification buttons, close them now
        try:
            element = browser.find_element(By.CSS_SELECTOR, 'a.esg-icon__container.esg-notification-center__close')
            element.click()
        except Exception:
            pass
        # Find and click the button
        button = browser.find_element(By.ID, 'register-button')  # Replace with the actual button's locator
        # Remove disabled attribute
        browser.execute_script("arguments[0].removeAttribute('disabled')", button)

        # Click button
        button.click()
        print("Clicking button")

        # Weight time to wait based on how close/far we are from deadline
        if (deadline - datetime.datetime.now() >= -45) and (deadline - datetime.datetime.now() > datetime.timedelta(minutes=5)):
            sync_sleep(10)
        else:
            sync_sleep(30)
    except Exception as error:
        print(f"Error occured! Will try again: {error}")
        sync_sleep(5)

browser.close()
print("Done!")