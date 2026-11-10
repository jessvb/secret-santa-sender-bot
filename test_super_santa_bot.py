import random
import unittest

from super_santa_bot import (check_assignment, days_until_christmas, get_families,
                             is_couple, is_parent_child, make_the_magic,
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
