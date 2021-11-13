########################################################
### This was made with help from freecodecamp.org <3 ###
########################################################

# smtplib is for creating an smtp client for emailing :)
import smtplib
# mimetext for emailing
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# for randomly selecting a secret recipient <3
import random

FILENAME_NAMES_EMAILS = "names_emails.csv"
FILENAME_EMAIL_OUTLINE = "email.txt"
FILENAME_HOST_EMAIL_AUTH = "host_email_auth.txt"

def get_names_emails(filename):
    parent_names = []
    parent_emails = []
    child_names = []
    child_emails = []
    with open(filename, mode='r', encoding='utf-8') as csv_file:
        for line in csv_file:
            parent_names.append(line.split(",")[0].split(" ")[0].strip())
            parent_emails.append(line.split(",")[1].strip())
            child_names.append(line.split(",")[2].split(" ")[0].strip())
            child_emails.append(line.split(",")[3].split("\n")[0].strip())
    return parent_names, parent_emails, child_names, child_emails

def read_email_outline(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_txt = template_file.read()
    return template_file_txt


def get_host_email_password(filename):
    with open(filename, 'r', encoding='utf-8') as txt_file:
        txt = txt_file.read()
        email = txt.split('\n')[0]
        password = txt.split('\n')[1]
    return (email, password)


def main():
    # get the names and email addresses of those you want to send to
    (parent_names, parent_emails, child_names, child_emails) = get_names_emails(FILENAME_NAMES_EMAILS)
    # names check
    for (parent_name, parent_email, child_name, child_email) in zip(parent_names, parent_emails, child_names, child_emails):
        print(parent_name + ', ' + parent_email + ', ' + child_name + ', ' + child_email)
    y_n = input('these are your people? (y/n) ')

    if (y_n == 'y' or y_n == 'yes' or y_n == 'Y' or y_n == 'Yes'):
        # get the credentials for the host email address
        (HOST_EMAIL, PASSWORD) = get_host_email_password(
            FILENAME_HOST_EMAIL_AUTH)
        # get the outline/template of the email you want to send
        email_outline = read_email_outline(FILENAME_EMAIL_OUTLINE)

        # set up the smtp client
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()
        s.login(HOST_EMAIL, PASSWORD)

        # personalize all the messages per-contact
        # for name, receiver_name, email in zip(names, receiver_names, emails):
        for parent_name, parent_email, child_name, child_email in zip(parent_names, parent_emails, child_names, child_emails):
            msg = MIMEMultipart()
            # substitute the ${GIVE_NAME} and ${REC_NAME} in the text
            text = email_outline.replace("${PARENT_NAME}", parent_name.title())
            text = text.replace("${CHILD_NAME}", child_name.title())
            text = "<html>\n<head></head>\n<body>\n" + text
            text = text + "\n</body>\n</html>"

            # set up the rest of the email parameters
            msg['From'] = 'Jessica Van Brummelen'
            msg['To'] = parent_email + ',' + child_email
            msg['Subject'] = "Future Worlds Challenge: Registration?"
            msg.add_header('reply-to', 'jess@csail.mit.edu')
            msg.attach(MIMEText(text, 'html'))

            # SEND IT!
            print("Sending to " + parent_email + " and " + child_email)
            s.send_message(msg)

            del msg

        # quit the smtp session and close the connection
        s.quit()

        print('Complete!')
    else:
        print("Hmm I guess those aren't the right people! Please edit names_emails.csv to fix.")


if __name__ == '__main__':
    main()
