# Daft.ie Automation
#### Video Demo:  <https://youtu.be/nx9n7UEIROo>
#### Description:

## Project Overview

Like many places in the world, Ireland is currently suffering from a severe housing crisis, and fuel has been added to the fire in recent months in the form of the government lifting a COVID-period eviction ban. My partner and I are among those who recently received an eviction notice, and we, along with thousands of others, are currently searching for a rental property. Daft.ie is Ireland's primary property website, with ~90% of all available properties being listed thereon. It is possible to save a set of search criteria on the website, and set up an email alert for when a property that fits those criteria is listed. However, if we do not see an email alert for an hour or two (sometimes less), in most cases the ad in question will already be taken down due to being inundated with responses. In the cases where we do manage to send a response, we are more than likely already hundreds of places down the list within a matter of minutes, and are extremely unlikely to get a response from the lessors. The idea for this project was to write a Python program that automates responses to property ads as soon as an email alert is received.

## Project Files

### project.py

This file contains the project's script, and is designed to run continuously in order to listen for property alert emails.

### test_project.py

This file contains the unit tests for the functions contained in project.py

### requirements.txt

This file contains the modules that must be pip installed in order for the main script to work.

### data/daft_creds.txt

This file should contain the user's Daft.ie credentials in the following format: "USERNAME/PASSWORD".

### data/daft_form.txt

This file should contain the user's information to be submitted in response to a given property ad in the following format: "FULL NAME\EMAIL\PHONE NUMBER\MESSAGE".

### data/gmail_creds.txt

This file should contain the user's gmail credentials in the following format: "USERNAME\PASSWORD".

### data/missed_ads.txt

This file will contain the URLs of any property ads to which the program could not respond for any reason, which can be checked by the user at a later point.

### testing/test_creds.txt

This file contains some dummy credentials to be used for testing purposes.

### testing/test_form.txt

This file contains some dummy form data to be used for testing purposes.

## Design

Broadly speaking, the program is designed to check whatever subsection of the user's gmail account to which property alert emails are directed, and if there are unread alerts, navigate to the URL of the property in question and post a response to the ad. There was a design issue in that Daft.ie requires the user to be logged into the website in order to respond to ads, and this proved extremely difficult and complicated with Python's requests module. After doing some research, it was determined that a login could be achieved by using the selenium and undetected-chromedriver modules to programmatically control a headless web browser.

### Functions

**main()**

This is the main function that is called at the bottom of the script. The function consists of an infinite loop that logs into the user's gmail account, checks their selected subsection once a minute 3 times, then repeats the loop, thereby re-initialising the connection to the user's gmail. It was discovered during testing that the connection to the gmail server gets dropped at some point overnight, so the finite loop that checks the user's selected mail subsection is designed to handle a dropped connection using a try/except block. If unread property alerts are found when the mail subsection is checked, the script will iterate over each alert, extract the URL for the ad, and post a response to the ad. If, for any reason, posting the response should fail, the program is designed to print the URL for the ad to "data/missed_ads.txt," such that the URL can be checked manually by the user at a later point. After each check, the script is set to wait for one minute.

**init_mail()**

This function is designed to initialise the connection to gmail's IMAP server, login to the user's gmail account, and return the resulting mail object.

**get_payload()**

This function is used a number of times, and is used to extract data from specified .txt files, such as login credentials, and form payloads. As specified above, the format of the .txt files should be set up so that pieces of data are separated by backslashes, and this allows the function to read the entirety of the .txt file into memory, call the split() method, and return the pieces of data as a list. The intention of this function is to allow the user to store sensitive information like usernames and passwords in .txt files, which is much more secure than hardcoding them into the script.

**check_inbox()**

This function takes the mail object as an argument, and is designed to search the user's selected mail subsection for unread property alert emails, and return a list of the relevant message numbers if unread alerts are found.

**get_url()**

This function takes the mail object and a message number as arguments, and is designed to fetch the data for the given message, create a string from said data, decode the resulting unicode text to plain text, and use regex to search the resulting HTML for the URL for the property ad in question. If such a URL is found, the function returns it.

**post_response()**

This function takes an extracted property ad URL as an argument. Firstly, the function creates an options object to be passed to the undetected-chromedriver object upon initialisation, and passes in the 'headless' argument. After this, the browser object is created with the options object passed in. The browser then requests the URL that was passed in, finds the button to click to accept cookies, clicks it, and waits a few seconds for the page to load. It then finds and clicks on the element that navigates to the login page. It was discovered during testing that cookies were required to access the login page, and it could not be accessed directly upon initialising the browser; hence, the initial navigation to the ad. The get_payload() function is then called to get the user's Daft.ie credentials, and passes the credentials to the form on the page. It then finds and clicks on the element to log in, and waits for the resulting page to load. Once the logged-in version of the ad page has loaded, the script then finds and clicks on the button to open the contact form. The get_payload() function is called once again in order to get the necessary data for the contact form. This data is passed to the form, and the button to send the data is then found and clicked on.