from daft import init_mail, get_payload, check_inbox, get_url


# Before running test, make sure there is ONE unread property alert email in your selected email folder


def test_init_mail():
    assert init_mail()


def test_get_payload():
    assert get_payload("testing/test_creds.txt") == ["USERNAME", "PASSWORD"]
    assert get_payload("testing/test_form.txt") == [
        "FULL NAME",
        "EMAIL",
        "PHONE NUMBER",
        "MESSAGE",
    ]


def test_check_inbox():
    mail = init_mail()
    mail.select("PropertyAlerts")
    assert len(check_inbox(mail)) == 1


def test_get_url():
    mail = init_mail()
    mail.select("PropertyAlerts")
    _, msg = mail.search(None, "(UNSEEN)", 'FROM "Daft.ie Property Alert"')
    assert get_url(mail, msg[0]).startswith("https://www.daft.ie/for-rent/")
