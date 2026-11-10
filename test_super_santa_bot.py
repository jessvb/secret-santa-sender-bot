import os
import random
import tempfile
import unittest

from super_santa_bot import (choose_group, find_email_outline, find_host_auth_file, init_group, list_groups,
                             check_assignment, days_until_christmas, get_families,
                             filter_to_names, is_couple, is_parent_child, mark_dry_run, make_the_magic,
                             render_email, validate_inputs)
from datetime import date

NAMES = ["Mary", "Joseph", "Rudolf", "Dasher", "Blitzen", "Mr. Claus", "Mrs. Claus"]
COUPLES = [("Mary", "Joseph"), ("Mr. Claus", "Mrs. Claus")]


class Matching(unittest.TestCase):
    def test_many_random_draws_are_valid(self):
        for seed in range(2000):
            r = make_the_magic(NAMES, COUPLES, rng=random.Random(seed))
            self.assertEqual(check_assignment(NAMES, r, COUPLES), [], seed)

    def test_tight_case_that_hung_the_old_algorithm(self):
        # 4 people, 2 couples: only valid draws are 'cross' pairings
        names = ["a", "b", "c", "d"]
        couples = [("a", "b"), ("c", "d")]
        for seed in range(500):
            r = make_the_magic(names, couples, rng=random.Random(seed))
            self.assertEqual(check_assignment(names, r, couples), [])

    def test_two_people_swap(self):
        self.assertEqual(make_the_magic(["a", "b"], []), ["b", "a"])

    def test_impossible_raises_instead_of_hanging(self):
        with self.assertRaises(ValueError):
            make_the_magic(["a", "b"], [("a", "b")])
        with self.assertRaises(ValueError):
            make_the_magic(["a"], [])

    def test_couples_case_insensitive(self):
        self.assertTrue(is_couple("MARY", "joseph", COUPLES))

    def test_checker_catches_bad_results(self):
        self.assertTrue(check_assignment(["a", "b"], ["a", "b"], []))      # self
        self.assertTrue(check_assignment(["a", "b", "c"], ["b", "b", "a"], []))  # dup
        self.assertTrue(check_assignment(["a", "b", "c"], ["b", "a", "c"], []))  # self c


KIDS = ["James", "Jude", "Jesus", "Elf1", "Elf2"]
FAMILIES = [(["Mary", "Joseph"], ["James", "Jude", "Jesus"]),
            (["Mr. Claus", "Mrs. Claus"], ["Elf1", "Elf2"])]
EVERYONE = NAMES + KIDS


class Families(unittest.TestCase):
    def test_parents_never_get_children_or_vice_versa(self):
        for seed in range(2000):
            r = make_the_magic(EVERYONE, COUPLES, FAMILIES, rng=random.Random(seed))
            self.assertEqual(check_assignment(EVERYONE, r, COUPLES, FAMILIES), [], seed)
            for g, rec in zip(EVERYONE, r):
                self.assertFalse(is_parent_child(g, rec, FAMILIES))

    def test_siblings_may_get_each_other(self):
        seen = any(
            (g in KIDS[:3] and rec in KIDS[:3])
            for seed in range(200)
            for g, rec in zip(EVERYONE, make_the_magic(
                EVERYONE, COUPLES, FAMILIES, rng=random.Random(seed))))
        self.assertTrue(seen)

    def test_single_parent_and_impossible(self):
        n, f = ["p", "c", "x", "y"], [(["p"], ["c"])]
        r = make_the_magic(n, [], f)
        self.assertEqual(check_assignment(n, r, [], f), [])
        # parent+child only: nobody can give to anyone else
        with self.assertRaises(ValueError):
            make_the_magic(["p", "c"], [], [(["p"], ["c"])])

    def test_checker_flags_parent_child(self):
        self.assertTrue(check_assignment(["p", "c", "x"], ["c", "x", "p"], [],
                                         [(["p"], ["c"])]))

    def test_validation(self):
        emails = [f"{n}@x.com" for n in "pcx"]
        with self.assertRaises(ValueError):
            validate_inputs(list("pcx"), emails, [], [(["p"], ["ghost"])])
        with self.assertRaises(ValueError):
            validate_inputs(list("pcx"), emails, [], [(["p"], ["p"])])

    def test_parse(self):
        import os, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# c\nMary, Joseph: James, Jude\nSolo: Kid\n")
        try:
            self.assertEqual(get_families(f.name),
                             [(["Mary", "Joseph"], ["James", "Jude"]), (["Solo"], ["Kid"])])
        finally:
            os.unlink(f.name)
        self.assertEqual(get_families("/nonexistent.txt"), [])


class DryRunSend(unittest.TestCase):
    def test_mark(self):
        subj, body = mark_dry_run("Hi", "<html>\n<head></head>\n<body>\nhello\n</body>\n</html>")
        self.assertEqual(subj, "DRY RUN: Hi")
        self.assertIn("<body>\n<p><strong>DRY RUN: </strong>", body)
        self.assertIn("hello", body)

    def test_filter(self):
        c, f = filter_to_names(["mary", "Jude", "Elf1"], COUPLES, FAMILIES)
        self.assertEqual(c, [])  # Joseph/Mr. Claus not on the list
        self.assertEqual(f, [(["Mary"], ["Jude"])])
        c, f = filter_to_names(["Mary", "Joseph", "Zed"], COUPLES, FAMILIES)
        self.assertEqual(c, [("Mary", "Joseph")])
        self.assertEqual(f, [])  # no kids on the list -> family dropped


class Groups(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = os.path.join(self.tmp.name, "additional_files")
        os.makedirs(os.path.join(self.base, "templates"))
        for f in ("names_emails.csv", "host_email_auth.txt", "email.html"):
            with open(os.path.join(self.base, "templates", f), "w") as fh:
                fh.write("template " + f)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_list_and_never_overwrite(self):
        self.assertEqual(list_groups(self.base), [])
        init_group("family 1", self.base)
        init_group("friends", self.base)
        self.assertEqual(list_groups(self.base), ["family 1", "friends"])  # not 'templates'
        path = os.path.join(self.base, "friends", "names_emails.csv")
        with open(path, "w") as fh:
            fh.write("my real data")
        init_group("friends", self.base)  # again
        self.assertEqual(open(path).read(), "my real data")

    def test_email_falls_back_to_template(self):
        init_group("g", self.base)
        gdir = os.path.join(self.base, "g")
        self.assertFalse(os.path.exists(os.path.join(gdir, "email.html")))  # not copied
        path, fallback = find_email_outline(gdir, self.base)
        self.assertTrue(fallback)
        self.assertEqual(path, os.path.join(self.base, "templates", "email.html"))
        with open(os.path.join(gdir, "email.html"), "w") as fh:
            fh.write("mine")
        path, fallback = find_email_outline(gdir, self.base)
        self.assertFalse(fallback)
        self.assertEqual(path, os.path.join(gdir, "email.html"))

    def test_shared_login_is_used_and_not_copied(self):
        with open(os.path.join(self.base, "host_email_auth.txt"), "w") as fh:
            fh.write("shared")
        init_group("g", self.base)
        self.assertFalse(os.path.exists(os.path.join(self.base, "g", "host_email_auth.txt")))
        self.assertEqual(find_host_auth_file(os.path.join(self.base, "g"), self.base),
                         os.path.join(self.base, "host_email_auth.txt"))
        # a group's own login wins
        with open(os.path.join(self.base, "g", "host_email_auth.txt"), "w") as fh:
            fh.write("own")
        self.assertEqual(find_host_auth_file(os.path.join(self.base, "g"), self.base),
                         os.path.join(self.base, "g", "host_email_auth.txt"))

    def test_bad_names_rejected(self):
        for bad in ("templates", "..", "a/b", ""):
            with self.assertRaises(ValueError):
                init_group(bad, self.base)

    def test_choose(self):
        with self.assertRaises(ValueError):
            choose_group(None, self.base)          # none yet
        init_group("only", self.base)
        self.assertEqual(choose_group(None, self.base), "only")   # single group: automatic
        self.assertEqual(choose_group("only", self.base), "only")
        with self.assertRaises(ValueError):
            choose_group("typo", self.base)


class Validation(unittest.TestCase):
    def test_duplicates_and_unknown_couples(self):
        with self.assertRaises(ValueError):
            validate_inputs(["a", "A"], ["a@x.com", "b@x.com"], [])
        with self.assertRaises(ValueError):
            validate_inputs(["a", "b"], ["a@x.com", "b@x.com"], [("a", "zed")])
        validate_inputs(["a", "b"], ["a@x.com", "b@x.com"], [])


class Email(unittest.TestCase):
    def test_variables_and_escaping(self):
        out = render_email("${GIVE_NAME}>${REC_NAME} ${NUM_DAYS_UNTIL_CHRISTMAS} "
                           "${NUM_DAYS_BEFORE_CHRISTMAS} ${WISHLISTS_LINK}",
                           "tom & jerry", "bob", 7, "http://x?a=1&b=2")
        self.assertIn("Tom &amp; Jerry>Bob 7 7 http://x?a=1&amp;b=2", out)

    def test_days_never_negative(self):
        self.assertEqual(days_until_christmas(date(2026, 12, 1)), 24)
        self.assertEqual(days_until_christmas(date(2026, 12, 30)), 0)


if __name__ == "__main__":
    unittest.main()
