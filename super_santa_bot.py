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
import shlex
import shutil
import ssl
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Layout:  additional_files/templates/   <- tracked example files
#          additional_files/<group>/     <- one folder per Secret Santa group (gitignored,
#                                           except its email.html)
#          additional_files/host_email_auth.txt  <- optional login shared by all groups
ADDITIONAL_FILES = "additional_files"
TEMPLATES_DIR = "templates"
DRY_RUN_PREFIX = "DRY RUN: "

# file names inside a group folder
F_EMAIL_OUTLINE = "email.html"
F_NAMES_EMAILS = "names_emails.csv"
F_DRY_RUN_NAMES_EMAILS = "dry_run_names_emails.csv"
F_HOST_EMAIL_AUTH = "host_email_auth.txt"
F_COUPLES = "couples.txt"
F_CHILDREN = "children.txt"
F_WISHLISTS = "wishlistslink.txt"
F_EMAIL_TITLE = "emailtitle.txt"

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


def list_groups(base=ADDITIONAL_FILES):
    """Names of the group folders (everything in additional_files/ but templates)."""
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base)
                  if d != TEMPLATES_DIR and not d.startswith(".")
                  and os.path.isdir(os.path.join(base, d)))


def init_group(name, base=ADDITIONAL_FILES):
    """Create base/<name>/ from base/templates/. Never overwrites existing files.
    The login file is skipped if a shared base/host_email_auth.txt exists."""
    if not re.fullmatch(r"[\w .-]+", name) or name in (TEMPLATES_DIR, ".", ".."):
        raise ValueError(f"{name!r} isn't a usable group name (letters, digits, space, - _ . only; "
                         f"and not {TEMPLATES_DIR!r})")
    src_dir, dst_dir = os.path.join(base, TEMPLATES_DIR), os.path.join(base, name)
    os.makedirs(dst_dir, exist_ok=True)
    for fname in sorted(os.listdir(src_dir)):
        dst = os.path.join(dst_dir, fname)
        if fname == F_EMAIL_OUTLINE:
            continue  # optional per group: without one, the template's is used
        if fname == F_HOST_EMAIL_AUTH and os.path.exists(os.path.join(base, F_HOST_EMAIL_AUTH)):
            print(f"  (skipped {fname}: using the shared {base}/{F_HOST_EMAIL_AUTH})")
        elif os.path.exists(dst):
            print(f"  kept existing {dst}")
        else:
            shutil.copyfile(os.path.join(src_dir, fname), dst)
            print(f"  created {dst}  <- now edit it")


def choose_group(requested=None, base=ADDITIONAL_FILES):
    """Pick the group folder: the one named on the command line, the only one
    there is, or one the user picks from a numbered list."""
    groups = list_groups(base)
    if requested:
        if requested not in groups:
            raise ValueError(f"no group folder {base}/{requested}/ (existing groups: "
                             f"{', '.join(groups) or 'none'}). Make one with "
                             f"`python super_santa_bot.py --init {shlex.quote(requested)}`")
        return requested
    if not groups:
        raise ValueError(f"no groups yet! Make one with `python super_santa_bot.py --init my-group`")
    if len(groups) == 1:
        return groups[0]
    print("Which Secret Santa group?")
    for i, g in enumerate(groups, 1):
        print(f"  {i}. {g}")
    while True:
        answer = input("number or name: ").strip()
        if answer in groups:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(groups):
            return groups[int(answer) - 1]
        print("  (not one of the groups, try again)")


def find_email_outline(group_dir, base=ADDITIONAL_FILES):
    """The group's own email.html if it has one, else the template's.
    Returns (path, is_template_fallback)."""
    own = os.path.join(group_dir, F_EMAIL_OUTLINE)
    if os.path.exists(own):
        return own, False
    return os.path.join(base, TEMPLATES_DIR, F_EMAIL_OUTLINE), True


def find_host_auth_file(group_dir, base=ADDITIONAL_FILES):
    """The group's own login file wins; otherwise the shared one."""
    for path in (os.path.join(group_dir, F_HOST_EMAIL_AUTH), os.path.join(base, F_HOST_EMAIL_AUTH)):
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"no {F_HOST_EMAIL_AUTH} in {group_dir}/ or {base}/")


def get_names_emails(filename):
    """Read `name,email[,email...]` rows. Returns (names, emails) where emails
    holds one list of addresses per person (repeats within a row are dropped)."""
    names, emails = [], []
    for row in csv.reader(read_data_lines(filename)):
        addresses = []
        for cell in row[1:]:
            cell = cell.strip()
            if cell and cell.lower() not in [a.lower() for a in addresses]:
                addresses.append(cell)
        if not row or not row[0].strip() or not addresses:
            raise ValueError(f"{filename}: expected 'name,email[,email...]', got {row!r}")
        names.append(row[0].strip())
        emails.append(addresses)
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


def get_families(filename):
    """Read `parent1, parent2: child1, child2, ...` rows (one family per line;
    one or more parents). Returns [(parents, children), ...]. A missing file
    just means 'no families'."""
    families = []
    try:
        lines = read_data_lines(filename)
    except FileNotFoundError:
        return families
    for line in lines:
        if line.count(":") != 1:
            raise ValueError(f"{filename}: expected 'parent1, parent2: child1, child2', got {line!r}")
        left, right = line.split(":")
        parents = [n.strip() for n in left.split(",") if n.strip()]
        children = [n.strip() for n in right.split(",") if n.strip()]
        if not parents or not children:
            raise ValueError(f"{filename}: need at least one parent and one child, got {line!r}")
        families.append((parents, children))
    return families


def get_host_email_password(filename):
    with open(filename, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    if len(lines) < 2:
        raise ValueError(f"{filename}: need email on line 1 and password on line 2")
    return lines[0].strip(), lines[1].strip()


def validate_inputs(names, emails, couples, families=()):
    """Catch input mistakes that would silently produce wrong pairings.

    Raises ValueError for fatal problems; returns a list of non-fatal warnings
    (e.g. a parent's email shared with their child).
    """
    if len(names) < 2:
        raise ValueError("need at least 2 participants")
    lowered = [n.lower() for n in names]
    dupes = sorted({n for n in lowered if lowered.count(n) > 1})
    if dupes:
        raise ValueError(f"duplicate names (pairing works by name): {dupes}")
    warnings = []
    owners = {}  # lowercased address -> people who list it
    for name, addresses in zip(names, emails):
        for e in addresses:
            owners.setdefault(e.lower(), []).append(name)
    for e, sharers in sorted(owners.items()):
        if len(sharers) < 2:
            continue
        warnings.append(f"{e} is shared by {', '.join(sharers)} (fine if a parent is "
                        f"receiving for their child; each person still gets their own email)")
    for e in (a for addresses in emails for a in addresses):
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e):
            raise ValueError(f"doesn't look like an email address: {e!r}")
    known = set(lowered)
    for a, b in couples:
        for n in (a, b):
            if n.lower() not in known:
                raise ValueError(f"couples file mentions {n!r}, who isn't in the names list")
        if a.lower() == b.lower():
            raise ValueError(f"couple pairs {a!r} with themself")
    for parents, children in families:
        for n in parents + children:
            if n.lower() not in known:
                raise ValueError(f"children file mentions {n!r}, who isn't in the names list")
        overlap = {p.lower() for p in parents} & {c.lower() for c in children}
        if overlap:
            raise ValueError(f"{sorted(overlap)} listed as both parent and child in the same family")
    return warnings


# ------------------------------------------------------------------ matching

def is_couple(name1, name2, couples):
    pair = {name1.strip().lower(), name2.strip().lower()}
    return any(pair == {a.strip().lower(), b.strip().lower()} for a, b in couples)


def is_parent_child(name1, name2, families):
    """True if one is a parent of the other (siblings are fine!)."""
    a, b = name1.strip().lower(), name2.strip().lower()
    for parents, children in families:
        ps = {p.strip().lower() for p in parents}
        cs = {c.strip().lower() for c in children}
        if (a in ps and b in cs) or (b in ps and a in cs):
            return True
    return False


def is_forbidden(name1, name2, couples, families=()):
    return (name1.strip().lower() == name2.strip().lower()
            or is_couple(name1, name2, couples)
            or is_parent_child(name1, name2, families))


def check_assignment(givers, receivers, couples, families=()):
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
        elif is_parent_child(giver, receiver, families):
            problems.append(f"{giver} has their parent/child {receiver}")
    return problems


def make_the_magic(names, couples, families=(), rng=random):
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
         if j != i and not is_forbidden(names[i], names[j], couples, families)]
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
                         "names, couples and children")
    receivers = [names[j] for j in chosen]
    problems = check_assignment(names, receivers, couples, families)
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


def mark_dry_run(subject, html_body):
    """Make test emails impossible to mistake for the official ones."""
    banner = (f"<p><strong>{DRY_RUN_PREFIX}</strong>"
              "(this is only a test of the Secret Santa Bot, not the official message!)</p>\n")
    return DRY_RUN_PREFIX + subject, html_body.replace("<body>\n", "<body>\n" + banner, 1)


def filter_to_names(names, couples, families):
    """For --dry-run-send, the test list is often a small stand-in for the real
    one. Keep only the couples/families made up of people on that list."""
    known = {n.lower() for n in names}
    kept_couples = [(a, b) for a, b in couples if a.lower() in known and b.lower() in known]
    kept_families = []
    for parents, children in families:
        ps = [x for x in parents if x.lower() in known]
        cs = [x for x in children if x.lower() in known]
        if ps and cs:
            kept_families.append((ps, cs))
    return kept_couples, kept_families


def build_message(host_email, to_emails, subject, html_body):
    """to_emails is a list of addresses; they all get the same message."""
    msg = MIMEMultipart("alternative")
    msg["From"] = host_email
    msg["To"] = ", ".join(to_emails)
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
        for to_emails, msg in messages:
            to_email = ", ".join(to_emails)
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
    parser.add_argument("group", nargs="?",
                        help=f"which group folder in {ADDITIONAL_FILES}/ to use "
                             "(asks you if there are several and you don't say)")
    parser.add_argument("--init", metavar="GROUP",
                        help=f"create a new group folder {ADDITIONAL_FILES}/GROUP/ from the templates")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="check inputs and make a valid draw, but send nothing "
                           "(prints the draw so you can eyeball it; real runs never do)")
    mode.add_argument("--dry-run-send", action="store_true",
                      help=f"like --dry-run, but really sends the emails to the people in "
                           f"{F_DRY_RUN_NAMES_EMAILS} (in the group folder) instead, "
                           f"marked '{DRY_RUN_PREFIX}'")
    args = parser.parse_args()
    dry = args.dry_run or args.dry_run_send
    if args.init:
        try:
            init_group(args.init)
        except ValueError as e:
            sys.exit(f"Oh no! {e}")
        print(f"Now edit the files in {ADDITIONAL_FILES}/{args.init}/, then run "
              f"`python super_santa_bot.py {shlex.quote(args.init)} --dry-run`")
        return
    try:
        group = choose_group(args.group)
    except ValueError as e:
        sys.exit(f"Oh no! {e}")
    gdir = os.path.join(ADDITIONAL_FILES, group)
    path = lambda fname: os.path.join(gdir, fname)  # noqa: E731
    print(f"Secret Santa group: {group}  ({gdir}/)")

    days = days_until_christmas()
    print(f"Only {days} days until Christmas!!!\n")

    wishlists_link = read_first_line(path(F_WISHLISTS))
    email_title = read_first_line(path(F_EMAIL_TITLE))

    if not confirm(f"this is the wishlists link {wishlists_link!r}?"):
        sys.exit(f"Edit {path(F_WISHLISTS)} to fix Santa Bot's memory.")
    if not confirm(f'this is the email title "{email_title}"?'):
        sys.exit(f"Edit {path(F_EMAIL_TITLE)} to fix Santa Bot's memory.")

    email_path, is_fallback = find_email_outline(gdir)
    if is_fallback:
        print(f"\n({gdir}/ has no {F_EMAIL_OUTLINE}, so the template one is used)")
    if not confirm(f"is this your email? {os.path.abspath(email_path)}"):
        sys.exit(f"Edit that file, or put your own {F_EMAIL_OUTLINE} in {gdir}/ to use instead.")

    names_file = path(F_DRY_RUN_NAMES_EMAILS if args.dry_run_send else F_NAMES_EMAILS)
    if args.dry_run_send:
        print(f"\n*** DRY RUN SEND: emails go ONLY to the people in {names_file}, "
              f"marked '{DRY_RUN_PREFIX}' ***\n")
    try:
        names, emails = get_names_emails(names_file)
    except FileNotFoundError:
        sys.exit(f"Couldn't find {names_file}. Copy it from "
                 f"{ADDITIONAL_FILES}/{TEMPLATES_DIR}/ and edit it.")
    which = ("the DRY RUN list (test recipients)" if args.dry_run_send
             else "the REAL list" + (" (nothing will be sent in a --dry-run)" if args.dry_run else ""))
    print(f"people from {names_file}, {which}:")
    for name, email in zip(names, emails):
        print(f"  {name}, {', '.join(email)}")
    if not confirm("these are your people?"):
        sys.exit(f"Edit {names_file} to fix Santa Bot's memory.")

    couples = get_couples(path(F_COUPLES))
    families = get_families(path(F_CHILDREN))
    if args.dry_run_send:
        couples, families = filter_to_names(names, couples, families)
        print("\n(dry run list: only couples/families made up of people on it are used)")
    print("\ncouples:")
    for a, b in couples:
        print(f"  {a} & {b}")
    if not confirm("these are your couples?"):
        sys.exit(f"Edit {path(F_COUPLES)} to fix Santa Bot's memory.")

    print("\nfamilies (parents can't get their children, or vice versa):")
    for parents, children in families:
        print(f"  {' & '.join(parents)} -> {', '.join(children)}")
    if not confirm("these are your families?"):
        sys.exit(f"Edit {path(F_CHILDREN)} to fix Santa Bot's memory.")

    try:
        warnings = validate_inputs(names, emails, couples, families)
        receivers = make_the_magic(names, couples, families)
    except ValueError as e:
        sys.exit(f"Oh no! {e}")
    for w in warnings:
        print(f"Warning: {w}")
    if warnings and not confirm("carry on anyway?"):
        sys.exit(f"Edit {names_file} to fix Santa Bot's memory.")
    print("ssb made the magic! everyone's paired up :)")

    if args.dry_run:
        host_email, password = "dry-run@example.com", ""
    else:
        try:
            host_email, password = get_host_email_password(find_host_auth_file(gdir))
        except (FileNotFoundError, ValueError) as e:
            sys.exit(f"Oh no! {e}")
    with open(email_path, encoding="utf-8") as f:
        email_outline = f.read()
    messages = []
    for giver, receiver, to_emails in zip(names, receivers, emails):
        body = render_email(email_outline, giver, receiver, days, wishlists_link)
        subject = email_title
        if args.dry_run_send:
            subject, body = mark_dry_run(subject, body)
        messages.append((to_emails, build_message(host_email, to_emails, subject, body)))

    if dry:
        print("\ndry run draw (shown ONLY because this is a dry run; a real run never prints this):")
        for giver, receiver in zip(names, receivers):
            print(f"  {giver} -> {receiver}")
        problems = check_assignment(names, receivers, couples, families)
        print("\nchecks:", "all passed ✅" if not problems else problems)
        if not args.dry_run_send:
            print(f"dry run: built {len(messages)} emails, sent none.")
            return
        if not confirm(f"send {len(messages)} '{DRY_RUN_PREFIX.strip()}' emails to the dry run list?"):
            sys.exit("Okay, nothing sent.")

    print("ssb just needs to make its merry way across the interwebs now...")
    sent, failed = send_all(host_email, password, messages)
    if args.dry_run_send:
        print(f"\nDry run send done: {len(sent)} sent"
              + (f", {len(failed)} FAILED: {', '.join(failed)}" if failed else "") + ".")
        sys.exit(1 if failed else 0)
    if failed:
        # Never print who-has-whom; just say who needs a manual follow-up.
        print(f"\nSent {len(sent)}, but {len(failed)} failed: {', '.join(failed)}")
        print("Re-running would re-draw for EVERYONE, so fix those by hand.")
        sys.exit(1)
    print("MERRY CHRISTMAS! The Secret Santa Bot has done its Super Secret Send!")


if __name__ == "__main__":
    main()
