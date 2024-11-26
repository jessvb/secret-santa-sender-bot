# 🎄🎁🎅 secret santa bot 🎅🎁🎄
Send anonymous emails 📧 to gift exchange participants 🤩 with the Secret Santa Bot 🎅! You'll never accidentally figure out who got who again! (Unless you're a hacker and you want to 👩‍💻🤖👨‍💻)

## how it works: user-level
The Secret Santa Bot takes a list of names and emails of gift-givers, automatically  decides who will be giving gifts to who, and sends them each emails with the name of their 🎁 Secret Gift Recipients 🎁! You can also give Santa Bot a list of couples 💑, so that the couples don't get each other (couples give gifts to each other anyways—let them enjoy giving to others 😉)

## how it works: hacker-level
1. Edit `email.html` with your personalized message to the gift-givers. You can use the following variables to refer to the people involved in the exchange, and other things:
    - `${GIVE_NAME}`: the name of the gift-giver (i.e., the name of the person receiving the email)
    - `${REC_NAME}`: the name of the person receiving the gift (i.e., the person who the email-receiver is *buying for*)
    - `${NUM_DAYS_UNTIL_CHRISTMAS}`: the number of days left until Christmas (based on the date the email is sent)
    - `${WISHLISTS_LINK}`: whatever text that you enter into the `wishlistslink.txt` file (you may want to put a link to a page with everyone's wishlists here, but it can really be anything!)
2. Copy the `names_emails.template.csv` file and rename it `names_emails.csv`:
```
cp additional_files/names_emails.template.csv additional_files/names_emails.csv
```
3. Edit the `names_emails.csv` file with the names (column 1) and corresponding email addresses (column 2) of the gift-givers

4. (Optional) Add a list of couples to `couples.txt` in the format:
```
Mary, Joseph
Mr. Claus, Mrs. Claus
```
5. (Optional) Add a link to a webpage that contains everyone's wishlists in `wishlistslink.txt`
6. Copy the `host_email_auth.template.txt` file and rename it `host_email_auth.txt`:
```
cp additional_files/host_email_auth.template.txt additional_files/host_email_auth.txt
```
7. Edit the `host_email_auth.txt` file with your credentials (email address you want the emails to be sent from on the first line, and password to that email on the next line)
    - Note: make sure your host email server allows less secure applications— Otherwise, you might get an error message like this, `smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted. Learn more at\n5.7.8`
    - For Gmail accounts, you can [allow less secure apps here](https://myaccount.google.com/lesssecureapps)
8. Add some Christmas cheer ✨ (Note: this step is **NOT OPTIONAL**!)
9. Let the Super Santa Bot do it's thing! In the root directory:
```
python super_santa_bot.py
```
    - In the console, a number of checks will come up; for example, a list of names and emails will appear
    - Make sure these are correct, and then type `y` and hit enter in the command line
    - Continue doing this until the Sender Bot is ready to send
And off into the world your emails will go! 🦌🦌🦌🦌🦌🛷🎅 Merry Christmas!

## notes and things to do
You might notice the code is not optimized speed-wise (it also doesn't need to be, assuming the Santa Bot only needs to visit a few dozen inboxes 😉), but feel free to contribute, if you feel like doing some Christmas-break optimization!

There's also a bug where it hangs— I haven't looked into what's actually going on here (probably some reindeer chomping on the code again 🌱 🦌 😅), but if you run into this, all you have to do is hit `ctrl+c` and re-run the program, and in all likelihood, Santa will get back to soaring 😉 
