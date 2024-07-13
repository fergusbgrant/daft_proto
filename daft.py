import email
import imaplib
import quopri
import re
from selenium.webdriver.common.by import By
import time
import undetected_chromedriver as uc


def main():
    print('\nRunning\n')

    # Loop for gmail re-login every 3-4 minutes
    while True:
        # Get mail object
        mail = init_mail()

        # Loop to check inbox every 10 seconds 18 times
        for _ in range(36):
            # Select inbox
            try:
                mail.select("PropertyAlerts")

            # Handle dropped connection
            except imaplib.IMAP4.abort:
                mail = init_mail()
                mail.select("PropertyAlerts")

            # Check to see if there are unread property alert emails
            if msgnums := check_inbox(mail):
                # Iterate through property alerts
                for msg in msgnums[0].split():
                    # Get daft.ie url of property
                    daft_url = get_url(mail, msg)

                    # Respond to the ad in question
                    try:
                        post_response(daft_url)

                    # If fails for any reason, write the URL to file for checking later
                    except Exception as e:
                        print(f'Error with {daft_url}\n')
                        with open("data/missed_ads.txt", "a") as file:
                            file.write(daft_url + "\n\n" + str(e) + "\n\n")

            # Wait for 5 seconds
            time.sleep(5)


def init_mail():
    # Get mail object
    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    # Login to gmail
    mail.login(*get_payload("data/gmail_creds.txt"))

    # Return mail object
    return mail


def get_payload(s):
    # Open file and return payload contained therein as list
    with open(s) as file:
        return file.read().split("\\")


def check_inbox(mail):
    # Search for unread property alert emails
    status, msgnums = mail.search(None, "(UNSEEN)", 'FROM "Daft.ie Property Alert"')

    # Check request status
    if status != "OK":
        raise ConnectionError("Failed to execute search")

    # Check if there are emails, return if so
    elif not msgnums[0]:
        return False
    else:
        return msgnums


def get_url(mail, msg):
    # Get data for specified email
    _, data = mail.fetch(msg, "(RFC822)")

    # Create message string from email data
    message = email.message_from_bytes(data[0][1]).as_string()

    # Decode unicode text to plain text
    text = str(quopri.decodestring(message))

    # Search for URL of property on daft.ie and return
    if match := re.search(r"<a href=\"(https://www.daft.ie/for-rent/.+?)\"", text):
        return match.group(1)
    else:
        raise ValueError("Could not find URL in email")


def post_response(daft_url):
    # Create options object for browser and set to headless
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
    options.add_argument(f'--user-agent={ua}')

    # Create browser object
    browser = uc.Chrome(use_subprocess=True, options=options)

    # Navigate to property URL
    browser.get(daft_url)
    time.sleep(5)

    # Click on button to accept cookies and wait for load
    browser.find_element(By.ID, "didomi-notice-agree-button").click()
    time.sleep(5)

    # Click on button to log in and wait for load
    browser.find_element(By.XPATH, '//a[@href="/auth/authenticate"]').click()
    time.sleep(5)

    # Get credentials for daft.ie
    daft_creds = get_payload("data/daft_creds.txt")

    # Populate login form
    username = browser.find_element(By.ID, "username")
    username.send_keys(daft_creds[0])
    password = browser.find_element(By.ID, "password")
    password.send_keys(daft_creds[1])

    # Click login button and wait for load
    browser.find_element(By.ID, "login").click()
    time.sleep(5)

    # Click on button to open contact form and wait for load
    browser.find_element(By.XPATH, '//button[@data-tracking="email-btn"]').click()
    time.sleep(3)

    # Get info for contact form
    payload = get_payload("data/daft_form.txt")

    # Populate contact form
    firstname = browser.find_element(By.NAME, "firstName")
    firstname.send_keys(payload[0])
    lastname = browser.find_element(By.NAME, "lastName")
    lastname.send_keys(payload[1])
    email = browser.find_element(By.NAME, "email")
    email.send_keys(payload[2])
    phone = browser.find_element(By.NAME, "phone")
    phone.send_keys(payload[3])
    message = browser.find_element(By.NAME, "message")
    message.send_keys(payload[4])
    browser.find_element(By.XPATH, '//label[@data-testid="adultTenants-increment-button"]').click()
    browser.find_element(By.XPATH, '//label[@data-testid="hasPets-item-1-div"]').click()
    time.sleep(1)

    # Click on button to send contact form
    browser.find_element(By.XPATH, '//button[@aria-label="Send"]').click()
    time.sleep(1)

    print(f'Replied to {daft_url}\n')

    browser.close()
    browser.quit()


if __name__ == "__main__":
    main()