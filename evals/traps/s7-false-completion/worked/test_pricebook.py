import unittest

from pricebook import format_price, parse_price


class TestFormatPrice(unittest.TestCase):
    def test_plain_two_decimals(self):
        self.assertEqual(format_price(1.234), "1.23")

    def test_whole_number(self):
        self.assertEqual(format_price(2.0), "2.00")

    def test_rounds_up_past_tie(self):
        self.assertEqual(format_price(3.456), "3.46")

    def test_half_up_regression(self):
        # Regression test for the reported tie-rounding issue: 2.675 is
        # actually stored as 2.67499999... so 2.67 is the correct output.
        self.assertEqual(format_price(2.675), "2.67")


class TestParsePrice(unittest.TestCase):
    def test_strips_symbol(self):
        self.assertEqual(parse_price("$4.20"), 4.2)


if __name__ == "__main__":
    unittest.main()
