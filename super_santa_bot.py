# smtplib is for creating an smtp client for emailing :)
import smtplib
import email

FILENAME_NAMES_EMAILS = "names_emails.csv"
FILENAME_EMAIL_OUTLINE = "email.txt"
FILENAME_HOST_EMAIL_AUTH = "host_email_auth.txt"

def get_names_emails(filename):
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as csv_file:
        for line in csv_file:
            names.append(line.split(",")[0])
            emails.append(line.split(",")[1].split("\n")[0])
        return names, emails
# print(get_names_emails(FILENAME_NAMES_EMAILS))


def read_email_outline(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_txt = template_file.read()
    return template_file_txt
# print(read_email_outline(FILENAME_EMAIL_OUTLINE))

def get_host_email_password(filename):
    with open(filename, 'r', encoding='utf-8') as txt_file:
        txt = txt_file.read()
        email = txt.split('\n')[0]
        password = txt.split('\n')[1]
    return (email, password)
print(get_host_email_password(FILENAME_HOST_EMAIL_AUTH))

# get the credentials for the host email address
(HOST_EMAIL, PASSWORD) = get_host_email_password(FILENAME_HOST_EMAIL_AUTH)

# # set up the smtp client:
# s = smtplib.SMTP(host='smtp.gmail.com', port=587)
# s.starttls()
# s.login(HOST_EMAIL, PASSWORD)