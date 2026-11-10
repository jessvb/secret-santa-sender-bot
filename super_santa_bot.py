########################################################
### This was made with help from freecodecamp.org <3 ###
########################################################

import argparse
import csv
import html
import os
import random
import re
import smtplib
import shutil
import ssl
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FILENAME_EMAIL_OUTLINE = "additional_files/email.html"
FILENAME_NAMES_EMAILS = "additional_files/names_emails.csv"
FILENAME_HOST_EMAIL_AUTH = "additional_files/host_email_auth.txt"
FILENAME_COUPLES = "additional_files/couples.txt"
FILENAME_WISHLISTS = "additional_files/wishlistslink.txt"
FILENAME_EMAIL_TITLE = "additional_files/emailtitle.txt"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------- file input

def read_data_lines(filename):
    """Non-blank lines of a config file, ignoring '#' comment lines. `utf-8-sig`
    transparently drops the BOM that Excel/Sheets put at the start of CSVs
    (the old code chopped the first letter off of the first name instead)."""
    with open(filename, encoding="utf-8-sig") as f:
        lines = [ln.strip() for ln in f]
    return [ln for ln in lines if ln and not ln.startswith("#")]


def read_first_line(filename):
    lines = read_data_lines(filename)
    if not lines:
        raise ValueError(f"{filename} is empty (only comments/blank lines)")
    return lines[0]


def init_files():
    """Copy each `x.template.y` to `x.y` unless `x.y` already exists."""
    for name in sorted(os.listdir("additional_files")):
        real = name.replace(".template", "")
        if real == name:
            continue
        src, dst = os.path.join("additional_files", name), os.path.join("additional_files", real)
        if os.path.exists(dst):
            print(f"  kept existing {dst}")
        else:
            shutil.copyfile(src, dst)
            print(f"  created {dst}  <- now edit it")


def get_names_emails(filename):
    """Read `name,email` rows."""
    names, emails = [], []
    for row in csv.reader(read_data_lines(filename)):
        if len(row) < 2 or not row[0].strip() or not row[1].strip():
            raise ValueError(f"{filename}: expected 'name,email', got {row!r}")
        names.append(row[0].strip())
        emails.append(row[1].strip())
    return names, emails


def get_couples(filename):
    """Read `name1,name2` rows. A missing file just means 'no couples'."""
    couples = []
    try:
        lines = read_data_lines(filename)
    except FileNotFoundError:
        return couples
    for row in csv.reader(lines):
        if len(row) != 2:
            raise ValueError(f"{filename}: expected 'name1,name2', got {row!r}")
        couples.append((row[0].strip(), row[1].strip()))
    return couples


def get_host_email_password(filename):
    with open(filename, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    if len(lines) < 2:
        raise ValueError(f"{filename}: need email on line 1 and password on line 2")
    return lines[0].strip(), lines[1].strip()


def validate_inputs(names, emails, couples):
    """Catch input mistakes that would silently produce wrong pairings."""
    if len(names) < 2:
        raise ValueError("need at least 2 participants")
    lowered = [n.lower() for n in names]
    dupes = sorted({n for n in lowered if lowered.count(n) > 1})
    if dupes:
        raise ValueError(f"duplicate names (pairing works by name): {dupes}")
    dupe_emails = sorted({e.lower() for e in emails if [x.lower() for x in emails].count(e.lower()) > 1})
    if dupe_emails:
        raise ValueError(f"duplicate email addresses: {dupe_emails}")
    for e in emails:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e):
            raise ValueError(f"doesn't look like an email address: {e!r}")
    known = set(lowered)
    for a, b in couples:
        for n in (a, b):
            if n.lower() not in known:
                raise ValueError(f"couples file mentions {n!r}, who isn't in the names list")
        if a.lower() == b.lower():
            raise ValueError(f"couple pairs {a!r} with themself")


# ------------------------------------------------------------------ matching

def is_couple(name1, name2, couples):
    pair = {name1.strip().lower(), name2.strip().lower()}
    return any(pair == {a.strip().lower(), b.strip().lower()} for a, b in couples)


def check_assignment(givers, receivers, couples):
    """Independently verify a result. Returns a list of problems (empty = ok)."""
    problems = []
    if sorted(givers) != sorted(receivers):
        problems.append("receivers are not a permutation of the givers "
                        "(someone gets two gifts, or nobody does)")
    for giver, receiver in zip(givers, receivers):
        if giver == receiver:
            problems.append(f"{giver} has themself")
        elif is_couple(giver, receiver, couples):
            problems.append(f"{giver} has their partner {receiver}")
    return problems


def make_the_magic(names, couples, rng=random):
    """Return receivers such that names[i] gives a gift to receivers[i].

    Randomized backtracking: for each giver we try the allowed receivers in
    random order and back up if we paint ourselves into a corner. Unlike
    "guess and restart", this always terminates, and finds an answer whenever
    one exists. Raises ValueError if no valid assignment exists.
    """
    n = len(names)
    order = list(range(n))
    rng.shuffle(order)  # the order we hand out receivers in
    allowed = [
        [j for j in range(n)
         if j != i and not is_couple(names[i], names[j], couples)]
        for i in range(n)
    ]
    # fewest-options-first makes dead ends show up early
    order.sort(key=lambda i: len(allowed[i]))
    chosen = [None] * n
    taken = [False] * n

    def assign(k):
        if k == n:
            return True
        giver = order[k]
        options = allowed[giver][:]
        rng.shuffle(options)
        for j in options:
            if not taken[j]:
                taken[j] = True
                chosen[giver] = j
                if assign(k + 1):
                    return True
                taken[j] = False
        return False

    if not assign(0):
        raise ValueError("no valid Secret Santa assignment exists with these "
                         "names and couples")
    receivers = [names[j] for j in chosen]
    problems = check_assignment(names, receivers, couples)
    assert not problems, problems  # should be impossible; never send bad data
    return receivers


# --------------------------------------------------------------------- email

def days_until_christmas(today=None):
    today = today or date.today()
    xmas = date(today.year, 12, 25)
    return max((xmas - today).days, 0)


def render_email(outline, giver, receiver, days, wishlists_link):
    """Fill in the template. Values are HTML-escaped so a name like
    'Tom & Jerry' can't break the markup."""
    text = outline
    for key, value in {
        "${GIVE_NAME}": giver.title(),
        "${REC_NAME}": receiver.title(),
        # README documents ..._UNTIL_...; older templates used ..._BEFORE_...
        "${NUM_DAYS_UNTIL_CHRISTMAS}": str(days),
        "${NUM_DAYS_BEFORE_CHRISTMAS}": str(days),
        "${WISHLISTS_LINK}": wishlists_link,
    }.items():
        text = text.replace(key, html.escape(value))
    return f"<html>\n<head><meta charset=\"utf-8\"></head>\n<body>\n{text}\n</body>\n</html>"


def html_to_plain(markup):
    text = re.sub(r"<br\s*/?>|</p>|</div>", "\n", markup, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def build_message(host_email, to_email, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["From"] = host_email
    msg["To"] = to_email
    msg["Subject"] = subject
    # plain text first, HTML last: clients show the last part they support
    msg.attach(MIMEText(html_to_plain(html_body), "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def send_all(host_email, password, messages):
    """Send every message over one connection. A failure for one recipient is
    recorded and skipped rather than aborting everyone after them. Returns
    (sent_to, failed) where failed maps address -> error."""
    sent, failed = [], {}
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as s:
        s.starttls(context=context)
        s.login(host_email, password)
        for to_email, msg in messages:
            try:
                s.send_message(msg)
                sent.append(to_email)
                print(f"  sent to {to_email}")
            except (smtplib.SMTPException, OSError) as e:
                failed[to_email] = str(e)
                print(f"  FAILED for {to_email}: {e}")
    return sent, failed


# ---------------------------------------------------------------------- main

def confirm(question):
    return input(question + " (y/n) ").strip().lower() in ("y", "yes")


def main():
    parser = argparse.ArgumentParser(description="Secret Santa Bot")
    parser.add_argument("--init", action="store_true",
                        help="create your real config files from the templates")
    parser.add_argument("--dry-run", action="store_true",
                        help="check inputs and make a valid draw, but send nothing "
                             "(assignments are never printed)")
    args = parser.parse_args()
    if args.init:
        init_files()
        return

    days = days_until_christmas()
    print(f"Only {days} days until Christmas!!!\n")

    wishlists_link = read_first_line(FILENAME_WISHLISTS)
    email_title = read_first_line(FILENAME_EMAIL_TITLE)

    if not confirm(f"this is the wishlists link {wishlists_link!r}?"):
        sys.exit(f"Edit {FILENAME_WISHLISTS} to fix Santa Bot's memory.")
    if not confirm(f'this is the email title "{email_title}"?'):
        sys.exit(f"Edit {FILENAME_EMAIL_TITLE} to fix Santa Bot's memory.")

    names, emails = get_names_emails(FILENAME_NAMES_EMAILS)
    for name, email in zip(names, emails):
        print(f"{name}, {email}")
    if not confirm("these are your people?"):
        sys.exit(f"Edit {FILENAME_NAMES_EMAILS} to fix Santa Bot's memory.")

    couples = get_couples(FILENAME_COUPLES)
    print("\ncouples:")
    for a, b in couples:
        print(f"  {a} & {b}")
    if not confirm("these are your couples?"):
        sys.exit(f"Edit {FILENAME_COUPLES} to fix Santa Bot's memory.")

    try:
        validate_inputs(names, emails, couples)
        receivers = make_the_magic(names, couples)
    except ValueError as e:
        sys.exit(f"Oh no! {e}")
    print("ssb made the magic! everyone's paired up :)")

    if args.dry_run:
        host_email, password = "dry-run@example.com", ""
    else:
        host_email, password = get_host_email_password(FILENAME_HOST_EMAIL_AUTH)
    with open(FILENAME_EMAIL_OUTLINE, encoding="utf-8") as f:
        email_outline = f.read()
    messages = []
    for giver, receiver, to_email in zip(names, receivers, emails):
        body = render_email(email_outline, giver, receiver, days, wishlists_link)
        messages.append((to_email, build_message(host_email, to_email, email_title, body)))

    if args.dry_run:
        print(f"dry run: built {len(messages)} emails, sent none.")
        return

    print("ssb just needs to make its merry way across the interwebs now...")
    sent, failed = send_all(host_email, password, messages)
    if failed:
        # Never print who-has-whom; just say who needs a manual follow-up.
        print(f"\nSent {len(sent)}, but {len(failed)} failed: {', '.join(failed)}")
        print("Re-running would re-draw for EVERYONE, so fix those by hand.")
        sys.exit(1)
    print("MERRY CHRISTMAS! The Secret Santa Bot has done its Super Secret Send!")


if __name__ == "__main__":
    main()
