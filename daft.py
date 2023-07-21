import email
import imaplib
import quopri
import re
from selenium.webdriver.common.by import By
import time
import undetected_chromedriver as uc


def main():
    # Loop for gmail re-login every 3-4 minutes
    while True:
        # Get mail object
        mail = init_mail()

        # Loop to check inbox once a minute 3 times
        for _ in range(3):
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
                    except Exception:
                        with open("data/missed_ads.txt", "a") as file:
                            file.write(daft_url + "\n")

            # Wait for one minute
            time.sleep(60)


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

    # Create browser object
    with uc.Chrome(use_subprocess=True, options=options) as browser:
        # Navigate to property URL
        browser.get(daft_url)

        # Click on button to accept cookies and wait for load
        browser.find_element(
            By.XPATH, '//button[@onclick="CookieConsent.acceptAll();"]'
        ).click()
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
        name = browser.find_element(By.NAME, "name")
        name.send_keys(payload[0])
        email = browser.find_element(By.NAME, "email")
        email.send_keys(payload[1])
        phone = browser.find_element(By.NAME, "phone")
        phone.send_keys(payload[2])
        message = browser.find_element(By.NAME, "message")
        message.send_keys(payload[3])
        browser.find_element(By.XPATH, '//button[@aria-label="adultTenants-increment"]').click()
        time.sleep(1)

        # Click on button to send contact form
        browser.find_element(By.XPATH, '//button[@aria-label="Send"]').click()


if __name__ == "__main__":
    main()
