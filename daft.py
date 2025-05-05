import email
import imaplib
import quopri
import re
from selenium.webdriver.common.keys import Keys
import time
import zendriver as zd
import asyncio


async def main():
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
                        await post_response(daft_url)

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
    if match := re.search(r"href=\"(https://www.daft.ie/for-rent/.+?)\"", text):
        return match.group(1)
    else:
        raise ValueError("Could not find URL in email")


async def post_response(daft_url):
    # Create browser object
    browser = await zd.start() #headless=True

    # Navigate to property URL
    tab = await browser.get(daft_url)
    time.sleep(2)

    #await tab.set_user_agent('Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36')

    # Click on button to accept cookies and wait for load
    await (await tab.find("didomi-notice-agree-button", best_match=True)).click()
    time.sleep(2)

    # Click on button to log in and wait for load
    await (await tab.find('//a[@href="/auth/authenticate"]', best_match=True)).click()
    time.sleep(2)

    # Get credentials for daft.ie
    daft_creds = get_payload("data/daft_creds.txt")

    # Populate login form
    await (await tab.find("username", best_match=True)).send_keys(daft_creds[0])
    await (await tab.find("password", best_match=True)).send_keys(daft_creds[1])

    # Click login button and wait for load
    await (await tab.find('//input[@value="SIGN IN"]', best_match=True)).click()
    time.sleep(2)

    # Click on button to open contact form and wait for load
    await (await tab.find('//button[@data-tracking="email-btn"]', best_match=True)).click()
    time.sleep(3)

    # Get info for contact form
    payload = get_payload("data/daft_form.txt")

    # Populate contact form
    await (await tab.find('//input[@id="keyword1"]', best_match=True)).send_keys(payload[0])
    await (await tab.find('//input[@id="keyword2"]', best_match=True)).send_keys(payload[1])
    await (await tab.find('//input[@id="keyword3"]', best_match=True)).send_keys(payload[2])
    await (await tab.find('//input[@id="keyword4"]', best_match=True)).send_keys(payload[3])
    await (await tab.find('//textarea[@id="message"]', best_match=True)).send_keys(payload[4])
    await (await tab.find('//button[@data-testid="adultTenants-increment-button"]', best_match=True)).click()
    await (await tab.find('//label[@data-testid="hasPets-item-1-div"]', best_match=True)).click()
    time.sleep(2)

    # Click on button to send contact form
    await (await tab.find('//button[@aria-label="Send"]', best_match=True)).click()
    time.sleep(5)

    print(f'Replied to {daft_url}\n')

    await tab.close()


if __name__ == "__main__":
    asyncio.run(main())