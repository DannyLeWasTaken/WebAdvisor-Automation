import datetime
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from dotenv import load_dotenv
import os
import subprocess
import wexpect
import atexit
import re
import json
import threading
import requests
load_dotenv()
# Specify your deadline time here (year, month, day, hour, minute)
deadline = datetime.datetime(2023, 11, 17, 8, 00)  # Example: Nov 17, 2023, at 15:00

API_URL = "http://localhost:8087"

# Webbrowser path and URL setup
driver_path = 'C:/Program Files/Mozilla Firefox/firefox.exe'
url = 'https://colleague-ss.uoguelph.ca/Student/Planning/DegreePlans'  # Replace with the URL of your login page

# Log back into Bitwarden using wexpect with a flexible expectation
def bitwarden_login():
    print("Bitwarden login")
    # Log in using Bitwarden
    login_process = subprocess.Popen(['bw', 'login', '--apikey'], stdin=subprocess.PIPE, text=True)
    login_process.communicate(input=f"{os.environ.get('BW_CLIENTID')}\n{os.environ.get('BW_CLIENTSECRET')}\n")
    login_process.wait()

    # Unlock using Bitwarden
    unlock_process = subprocess.Popen(['bw', 'unlock'], stdin=subprocess.PIPE, text=True)
    unlock_process.communicate(input=f"{os.environ.get('BW_PASSWORD')}\n")
    unlock_process.wait()

def bitwarden_logout():
    subprocess.run(['bw', 'logout'])
    print("Logged out of Bitwarden")

def sync_sleep(interval):
    now = datetime.datetime.now()
    sleep_time = interval - (now.second % interval)
    time.sleep(sleep_time)
    

# Bind ending the program to logging out of bitwarden
atexit.register(bitwarden_logout)

# Start a browser session
browser = webdriver.Firefox()
browser.get(url)

def get_element_or_wait(element_id):
    element = browser.find_element(By.ID, element_id)
    if element:
        return element
    else:
        wait = WebDriverWait(browser, 10)
        wait.until(EC.presence_of_element_located((By.ID, element_id)))
        return browser.find_element(By.ID, element_id)

def is_microsoft_login_page(url):
    pattern = r"https:\/\/(.*\.)?login\.live\.com|https:\/\/(.*\.)?login\.microsoftonline\.com"
    return re.match(pattern, url) is not None

# login into microsoft
def microsoft_login(browser):
    bitwarden_login() 
    print("Logging in through Microsoft")

    #serve_process = subprocess.Popen(['bw', 'serve'], stdin=subprocess.PIPE, text=True)
    process_holder = []
    def run_bw_serve():
        proc = subprocess.Popen(['bw', 'serve'], text=True)
        return proc
    
    thread = threading.Thread(target=lambda: process_holder.append(run_bw_serve()))
    thread.start()
    payload = {
        "password": os.environ.get("BW_PASSWORD")
    }

    # Unlock vault
    response = requests.post(API_URL + "/unlock", json=payload, headers = {"Content-Type": 'application/json'}) 
    if response.status_code == 200:
        print("Vault unlocked successfully.")
    else:
        print(f"Failed to unlock vault: {response.status_code}")

    # Get passwords + email
    email = requests.get(API_URL + f"/object/username/{os.environ.get('BW_ID')}", headers = {"Content-Type": "application/json"}).json()["data"]["data"]
    password = requests.get(API_URL + f"/object/password/{os.environ.get('BW_ID')}", headers = {"Content-Type": "application/json"}).json()["data"]["data"]

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "i0116"))
    )

    # Submit to email field
    while True:
        try:
            email_field = email_field = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "i0116"))  # ID for the email field on the Microsoft login page
            )
            email_field.send_keys(email)
            next_button = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "idSIButton9"))
            )
            next_button.click()
            time.sleep(1)
            if not EC.element_to_be_clickable((By.ID, "i0118")):
                break
        except Exception:
            break;
    
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.ID, "i0118"))
    )

    # Wait for the password field and input password
    while True:
        try:
            password_field = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "i0118"))  # ID for the password field on the Microsoft login page
            )
            password_field.send_keys(password)
            next_button = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "idSIButton9"))
            )
            next_button.click()
            time.sleep(1)
            if not EC.element_to_be_clickable((By.ID, "i0118")):
                break
        except Exception:
            break;
    
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "idTxtBx_SAOTCC_OTC"))
    )

    # Do 2fa
    while True:
        try:
            totp_field = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "idTxtBx_SAOTCC_OTC"))
            )
            totp = requests.get(API_URL + f"/object/totp/{os.environ.get('BW_ID')}", headers = {"Content-Type": "application/json"}).json()["data"]["data"]
            totp_field.send_keys(totp)
            next_button = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "idSubmit_SAOTCC_Continue"))
            )
            next_button.click()
            time.sleep(1)
            if not EC.element_to_be_clickable((By.ID, "idTxtBx_SAOTCC_OTC")):
                break
        except Exception:
            break;
    # Stop serving
    if process_holder:
        try:
            process_holder[0].terminate()
            thread.join()
        except Exception:
            pass
    # Logout of bitwarden now
    bitwarden_logout()

    while is_microsoft_login_page(browser.current_url):
        time.sleep(0.1)

# Navigate to webadvisor
def navigate_webadvisor(browser):
    # Microsoft page was detected!
    browser.set_window_size(1024, 768)
    print("Detected page is")
    if is_microsoft_login_page(browser.current_url):
        microsoft_login(browser)
    browser.get(url)
    next_semester = WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.ID, "schedule-next-term"))
    )
    browser.execute_script("arguments[0].scrollIntoView();", next_semester)
    ActionChains(browser).move_to_element(next_semester).click(next_semester).perform()

# Automated login
def start(browser):
    microsoft_login(browser)
    navigate_webadvisor(browser)

start(browser)

print("Starting loop...")
# Calculate the start time (2 minutes before the deadline)
start_time = deadline - datetime.timedelta(minutes=2)

# Wait until the start time is reached
while datetime.datetime.now() < start_time:
    sync_sleep(10)  # Check every 10 seconds

def is_browser_alive(browser):
    try:
        browser.current_url
        return True
    except Exception:
        return False


# Main process - starts 2 minutes before the deadline
while datetime.datetime.now() < deadline:
    # Do some sanity checks first

    # Browser no longer exists...?
    if not is_browser_alive(browser):
        print("Browser died. Rebooting.")
        try:
            browser = webdriver.Firefox()
            browser.get(url)
            WebDriverWait(browser, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            start(browser)
        except Exception as err:
            print(f"Failed to reboot. Trying again in 5 seconds. Error due to: {err}")
            time.sleep(5)
            continue


    # Ensure we stay on the same page no matter what
    if browser.current_url != url:
        print("Url does not match. Redirecting.")
        try:
            browser.get(url)
            WebDriverWait(browser, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            navigate_webadvisor(browser)
            continue;
        except Exception as err:
            print(f"Failed to get browser due to: {err}")
            continue

    try:
        # If there exists any pre-existing notification buttons, close them now
        try:
            element = browser.find_element(By.CSS_SELECTOR, 'a.esg-icon__container.esg-notification-center__close')
            ActionChains(browser).move_to_element(element).click(element).perform()
            element.click()
        except Exception:
            pass
        # Find and click the button
        button = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "register-button"))
        )
        # Remove disabled attribute
        browser.execute_script("arguments[0].removeAttribute('disabled')", button)
        ActionChains(browser).scroll_to_element(button).click(button).perform
        print("Clicking button")

        time_difference = datetime.datetime.now() - start_time

        # Check if we are within 5 minutes before the deadline or up to 1 hour after the deadline
        if datetime.timedelta(minutes=-5) <= time_difference <= datetime.timedelta(hours=1):
            sync_sleep(10)  # Within the specified time range, sleep for 10 seconds
        else:
            sync_sleep(30)  # Outside the specified time range, sleep for 30 seconds
    except Exception as error:
        print(f"Error occured! Will try again: {error}")
        sync_sleep(5)

browser.close()
print("Done!")