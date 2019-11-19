########################################################
### This was made with help from freecodecamp.org <3 ###
########################################################

# smtplib is for creating an smtp client for emailing :)
import smtplib
# mimetext for emailing
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
# print(get_host_email_password(FILENAME_HOST_EMAIL_AUTH))

def main():
    # get the credentials for the host email address
    (HOST_EMAIL, PASSWORD) = get_host_email_password(FILENAME_HOST_EMAIL_AUTH)
    # get the names and email addresses of those you want to send to
    (names, emails) = get_names_emails(FILENAME_NAMES_EMAILS)
    # get the outline/template of the email you want to send
    email_outline = read_email_outline(FILENAME_EMAIL_OUTLINE)

    # print(email_outline.replace("${REC_NAME}", 'the beautiful rec name'))

    # set up the smtp client
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(HOST_EMAIL, PASSWORD)

    # personalize all the messages per-contact
    for name, email in zip(names, emails):
        msg = MIMEMultipart()
        # substitute the ${GIVE_NAME} and ${REC_NAME} in the text
        text = email_outline.replace("${GIVE_NAME}", name.title())
        text = text.replace("${REC_NAME}", "TODO")

        # set up the rest of the email parameters
        msg['From']=HOST_EMAIL
        msg['To']=email
        msg['Subject']="Test email 3"
        msg.attach(MIMEText(text, 'plain'))

        # SEND IT!
        s.send_message(msg)

        del msg
    
    # quit the smtp session and close the connection
    s.quit()

    print('MERRY CHRISTMAS! The Secret Santa Bot has done its Super Secret Send!')

if __name__ == '__main__':
    main()