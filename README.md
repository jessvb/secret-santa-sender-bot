# email sender bot
Automate sending emails to parent/child participants.

## how it works
1. Edit `email.txt` with your HTML message. You can use the following variables to refer to the people involved in the exchange: `${PARENT_NAME}` and `${CHILD_NAME}`.
2. Copy the `names_emails.template.csv` file and rename it `names_emails.csv`:
```
cp names_emails.template.csv names_emails.csv
```
3. Edit the `names_emails.csv` file with the names (column 1) and corresponding email addresses (column 2) of the parents, and the names (column 3) and corresponding email addresses (column 4) of the children
4. Copy the `host_email_auth.template.txt` file and rename it `host_email_auth.txt`:
```
cp host_email_auth.template.txt host_email_auth.txt
```
5. Edit the `host_email_auth.txt` file with your credentials (email address you want the emails to be sent from on the first line, and password to that email on the next line)
    - Note: make sure your host email server allows less secure applications— Otherwise, you might get an error message like this, `smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted. Learn more at\n5.7.8`
    - For Gmail accounts, you can [allow less secure apps here](https://myaccount.google.com/lesssecureapps). (Note: if you have 2-factor authentication turned on, make sure to first turn it off.)
6. Let the Email Sender Bot do it's thing! In the root directory:
```
python email_sender.py
```
    - In the console, a list of names and emails will appear
    - Make sure these are correct, and then type `y` and hit enter in the command line
