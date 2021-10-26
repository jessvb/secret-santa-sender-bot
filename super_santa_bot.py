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
FILENAME_COUPLES = "couples.txt"


def get_couples(filename):
    couples = []
    with open(filename, mode='r', encoding='utf-8') as couples_file:
        for line in couples_file:
            couples.append([line.split(",")[0].strip(),
                            line.split(",")[1].strip()])
    return couples


def get_names_emails(filename):
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as csv_file:
        for line in csv_file:
            names.append(line.split(",")[0].strip())
            emails.append(line.split(",")[1].split("\n")[0].strip())
    return names, emails


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

# make sure couples aren't paired up
def is_couple(name1, name2, couples):
    isCoup = False
    for couple in couples:
        if(name1 == couple[0] and name2 == couple[1] or name1 == couple[1] and name2 == couple[0]):
            isCoup = True
    return isCoup

# the secret santa selection!
def make_the_magic(names, couples):
    done = False

    while (done == False):
        print('trying to make the magic! (attempting to pair everyone up...)')
        secret_names = []
        temp_names = names.copy()
        while len(temp_names) > 1:
            ind = random.randrange(len(temp_names))
            receiver = temp_names[ind]
            giver = names[len(secret_names)]
            # make sure that the giver name != receiver name
            # and that there are no couples paired together
            while (receiver == giver or is_couple(receiver, giver, couples)):
                ind = random.randrange(len(temp_names))
                receiver = temp_names[ind]
            # add the receiver to the secret_names list
            # and remove the receiver from temp_names
            secret_names.append(temp_names.pop(ind))
        # if the last two names aren't the same,
        # and aren't a couple, then we're done!
        # otherwise, restart
        if (temp_names[0] != names[-1] and not (is_couple(temp_names[0], names[-1], couples))):
            secret_names.append(temp_names.pop())
            done = True
        else:
            print('That didn\'t quite work. Let me try again!')

    return secret_names


def main():
    # get the names and email addresses of those you want to send to
    (names, emails) = get_names_emails(FILENAME_NAMES_EMAILS)
    # names check
    for (name, email) in zip(names, emails):
        print(name + ', ' + email)
    y_n = input('these are your people? (y/n) ')
    if (y_n == 'y' or y_n == 'yes' or y_n == 'Y' or y_n == 'Yes'):
        # get the couples
        couples = get_couples(FILENAME_COUPLES)
        # couples check
        print('\ncouples:')
        for couple in couples:
            print(couple)
        print('\ncouples comparison test (this should print all True couples twice):')
        for name1 in names:
            for name2 in names:
                if (name1 != name2):
                    if (is_couple(name1,name2,couples)):
                        print(f'    {name1} {name2} is couple? {is_couple(name1,name2,couples)}')

        y_n = input('these are your couples? (y/n) ')
        if (y_n == 'y' or y_n == 'yes' or y_n == 'Y' or y_n == 'Yes'):
            # get the credentials for the host email address
            (HOST_EMAIL, PASSWORD) = get_host_email_password(
                FILENAME_HOST_EMAIL_AUTH)
            # get the outline/template of the email you want to send
            email_outline = read_email_outline(FILENAME_EMAIL_OUTLINE)

            receiver_names = make_the_magic(names, couples)
            print("ssb made the magic! everyone's paired up :)")
            print("ssb just needs to make its merry way across the interwebs now...")

            # set up the smtp client
            s = smtplib.SMTP(host='smtp.gmail.com', port=587)
            s.starttls()
            s.login(HOST_EMAIL, PASSWORD)

            # personalize all the messages per-contact
            for name, receiver_name, email in zip(names, receiver_names, emails):
                msg = MIMEMultipart()
                # substitute the ${GIVE_NAME} and ${REC_NAME} in the text
                text = email_outline.replace("${GIVE_NAME}", name.title())
                text = text.replace("${REC_NAME}", receiver_name.title())
                text = "<html>\n<head></head>\n<body>\n" + text
                text = text + "\n</body>\n</html>"

                # set up the rest of the email parameters
                msg['From'] = HOST_EMAIL
                msg['To'] = email
                msg['Subject'] = "Super Secret Santa Bot Message for Youuuu!"
                msg.attach(MIMEText(text, 'html'))

                # SEND IT!
                s.send_message(msg)

                del msg

            # quit the smtp session and close the connection
            s.quit()

            print('MERRY CHRISTMAS! The Secret Santa Bot has done its Super Secret Send!')
        else:
            print(
                "Oh no! Santa Bot messed up! Edit the couples.txt file to fix its memory.")
    else:
        print(
            "Oh no! Santa Bot messed up! Edit the names_emails.csv file to fix its memory.")


if __name__ == '__main__':
    main()
