# 🎄🎁🎅 secret santa bot 🎅🎁🎄
Send anonymous emails 📧 to gift exchange participants 🤩 with the Secret Santa Bot 🎅! You'll never accidentally figure out who got who again! (Unless you're a hacker and you want to 👩‍💻🤖👨‍💻)

## how it works: user-level
The Secret Santa Bot takes a list of names and emails of gift-givers, automatically  decides who will be giving gifts to who, and sends them each emails with the name of their 🎁 Secret Gift Recipients 🎁! You can also give Santa Bot a list of couples 💑, so that the couples don't get each other (couples give gifts to each other anyways—let them enjoy giving to others 😉), and a list of families 👨‍👩‍👧‍👦, so that parents don't get their own kids (and kids don't get their own parents)—but siblings are fair game! 😈

## how it works: hacker-level
1. Create your real config files from the templates (existing files are never overwritten, so it's safe to run again):
```
python super_santa_bot.py --init
```
   Every file below lives in `additional_files/`. The `*.template.*` files are tracked in git (they're just examples!); the real copies are in `.gitignore`, so your friends' emails, your password, and your secret links never get committed. In the names, couples, children, link, and subject files, lines starting with `#` are comments (the templates use them to explain themselves).
2. `names_emails.csv`: names (column 1) and email addresses (column 2) of the gift-givers, one per line. Names must be unique.
3. `couples.txt` (optional): pairs who shouldn't get each other, in the format below (delete the examples if you have no couples):
```
Mary, Joseph
Mr. Claus, Mrs. Claus
```
4. `children.txt` (optional): families, one per line, with the parents on the left of the colon and the kids on the right. Parents can't get their kids and kids can't get their parents (in either direction!), but siblings can still get each other. A single parent is fine too (just put one name before the colon):
```
Mary, Joseph: James, Jude, Jesus
Mr. Claus, Mrs. Claus: Elf1, Elf2
```
   Everyone has to be in `names_emails.csv`, and (like couples) names are matched ignoring upper/lowercase. Delete the examples if nobody has kids.
5. `wishlistslink.txt`: a link to a page with everyone's wishlists (it can really be anything!), and `emailtitle.txt`: the email subject line. Only the first non-comment line of each is used.
6. `host_email_auth.txt`: the email address you want the emails sent from on the first line, and its password on the second (no comments allowed in this one, in case your password starts with a `#`!)
    - For Gmail accounts, you need to [add 2-step verification](https://myaccount.google.com/signinoptions/two-step-verification), create an [app password for the Santa Bot](https://myaccount.google.com/apppasswords), and enter this app password instead of your account password. Otherwise you'll get `smtplib.SMTPAuthenticationError: (535, ...Username and Password not accepted`.
7. `email.html`: your personalized message. This one is the odd one out: it's **committed on purpose** (no template, and not gitignored), so we can look back at every year's email 📜. That also means: never paste private links straight into it—use `${WISHLISTS_LINK}` and keep the real link in the gitignored `wishlistslink.txt`. Edit it each year! You can use these variables:
    - `${GIVE_NAME}`: the name of the gift-giver (i.e., the person receiving the email)
    - `${REC_NAME}`: the name of the person they are *buying for*
    - `${NUM_DAYS_UNTIL_CHRISTMAS}`: days left until Christmas (based on the date the email is sent)
    - `${WISHLISTS_LINK}`: the text from `wishlistslink.txt`
8. Add some Christmas cheer ✨ (Note: this step is **NOT OPTIONAL**!)
9. (Recommended) Take a practice lap! This checks everything, makes a draw, and prints who-gives-to-who so you can eyeball it (spoilers! 🙈), but sends nothing. A real run never prints the pairs. (`--dry-run` and `--dry-run-send` can't be combined; pick one!)
```
python super_santa_bot.py --dry-run
```
10. (Also recommended) Do a dress rehearsal with *real* emails! `dry_run_names_emails.csv` (same `name,email` format as `names_emails.csv`) is a separate list of test recipients—put in a few addresses you can read yourself (like `you+mary@gmail.com`). Then:
```
python super_santa_bot.py --dry-run-send
```
    This does a dry run (prints the draw, just like `--dry-run`), then—after asking one more time—actually sends the emails, but **only** to the people on the dry-run list, with `DRY RUN: ` stuck on the front of the subject and the start of the email so nobody mistakes them for the real thing. Your real `names_emails.csv` isn't touched. The draw is made among the dry-run people, and only the couples/families from your real files who are *all* on the dry-run list get applied (so keep a few real names on it if you want to see those rules in action!). Heads up: it does use your real `host_email_auth.txt`, since it really sends. The dry-run list is gitignored too, of course.
11. Let the Super Santa Bot do its thing! In the root directory:
```
python super_santa_bot.py
```

- In the console, a number of checks will come up; for example, a list of names and emails will appear
- Make sure these are correct, and then type `y` and hit enter in the command line
- Next, a list of couples will appear—Make sure they're correct and hit `y` and enter
- Then a list of families will appear (parents -> kids)—check it and hit `y` and enter
- Continue doing this until the Sender Bot is ready to send
- If something's off, the bot tells you which file to fix. It also refuses to play if names are duplicated, a couple or family mentions someone who isn't playing, or an email address looks funny—and if the couples and families make a fair draw impossible (like only two people who are a couple, or a parent and their one child), it says so instead of getting stuck 🦌💤

And off into the world your emails will go! 🦌🦌🦌🦌🦌🛷🎅 Merry Christmas!

## notes and things to do
You might notice the code is not optimized speed-wise (it also doesn't need to be, assuming the Santa Bot only needs to visit a few dozen inboxes 😉), but feel free to contribute, if you feel like doing some Christmas-break optimization!

Run the tests with `python -m unittest` (they check that nobody ever gets themself, their partner, or their parent/child, and that everyone gives and receives exactly once ✅).

If some emails fail to send, the bot lists the addresses (not who got whom) so you can follow up by hand. Don't just re-run it, though—that would re-draw for EVERYONE and mess up the ones that already went out 🙈

(The old "it hangs sometimes" bug is fixed—it was Santa Bot getting stuck trying to match someone with only their partner left. No more reindeer chomping 🌱🦌)
