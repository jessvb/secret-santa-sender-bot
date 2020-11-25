# 🎄🎁🎅 secret santa bot 🎅🎁🎄
Send anonymous emails 📧 to gift exchange participants 🤩 with the Secret Santa Bot 🎅! You'll never accidentally figure out who got who again! (Unless you're a hacker and you want to 👩‍💻🤖👨‍💻)

## how it works: user-level
The Secret Santa Bot takes a list of names and emails of gift-givers, automatically  decides who will be giving gifts to who, and sends them each emails with the name of their 🎁 Secret Gift Recipients 🎁! You can also give Santa Bot a list of couples 💑, so that the couples don't get each other (couples give gifts to each other anyways—let them enjoy giving to others 😉)

## how it works: hacker-level
1. Edit `email.txt` with your personalized message to the gift-givers. You can use the following variables to refer to the people involved in the exchange:
    - `${GIVE_NAME}`: the name of the gift-giver (i.e., the name of the person receiving the email)
    - `${REC_NAME}`: the name of the person receiving the gift (i.e., the person who the email-receiver is *buying for*)
2. Copy the `names_emails.template.csv` file and rename it `names_emails.csv`:
```
cp names_emails.template.csv names_emails.csv
```
3. Edit the `names_emails.csv` file with the names (column 1) and corresponding email addresses (column 2) of the gift-givers

4. (Optional) Add a list of couples to `couples.txt` in the format:
```
Mary, Joseph
Mr. Claus, Mrs. Claus
```
5. Copy the `host_email_auth.template.txt` file and rename it `host_email_auth.txt`:
```
cp host_email_auth.template.txt host_email_auth.txt
```
6. Edit the `host_email_auth.txt` file with your credentials (email address you want the emails to be sent from on the first line, and password to that email on the next line)
    - Note: make sure your host email server allows less secure applications— Otherwise, you might get an error message like this, `smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted. Learn more at\n5.7.8`
    - For Gmail accounts, you can [allow less secure apps here](https://myaccount.google.com/lesssecureapps)
7. Add some Christmas cheer ✨ (Note: this step is **NOT OPTIONAL**!)
8. Let the Super Santa Bot do it's thing! In the root directory:
```
python super_santa_bot.py
```
    - In the console, a list of names and emails will appear
    - Make sure these are correct, and then type `y` and hit enter in the command line
    - Next, a list of couples will appear—Make sure they're correct and hit `y` and enter
And off into the world your emails will go! 🦌🦌🦌🦌🦌🛷🎅 Merry Christmas!

## notes and things to do
You might notice the code is not optimized speed-wise (it also doesn't need to be, assuming the Santa Bot only needs to visit a few dozen inboxes 😉), but feel free to contribute, if you feel like doing some Christmas-break optimization!

There's also a bug where it hangs— I haven't looked into what's actually going on here (probably some reindeer chomping on the code again 🌱 🦌 😅), but if you run into this, all you have to do is hit `ctrl+c` and re-run the program, and in all likelihood, Santa will get back to soaring 😉 
