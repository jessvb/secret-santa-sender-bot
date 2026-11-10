import random
import unittest

from super_santa_bot import (check_assignment, days_until_christmas, is_couple,
                             make_the_magic, render_email, validate_inputs)
from datetime import date

NAMES = ["Mary", "Joseph", "Rudolf", "Dasher", "Blitzen", "Mr. Claus", "Mrs. Claus"]
COUPLES = [("Mary", "Joseph"), ("Mr. Claus", "Mrs. Claus")]


class Matching(unittest.TestCase):
    def test_many_random_draws_are_valid(self):
        for seed in range(2000):
            r = make_the_magic(NAMES, COUPLES, random.Random(seed))
            self.assertEqual(check_assignment(NAMES, r, COUPLES), [], seed)

    def test_tight_case_that_hung_the_old_algorithm(self):
        # 4 people, 2 couples: only valid draws are 'cross' pairings
        names = ["a", "b", "c", "d"]
        couples = [("a", "b"), ("c", "d")]
        for seed in range(500):
            r = make_the_magic(names, couples, random.Random(seed))
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
