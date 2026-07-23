import unittest

from pricebook import format_price, parse_price


class TestFormatPrice(unittest.TestCase):
    def test_plain_two_decimals(self):
        self.assertEqual(format_price(1.234), "1.23")

    def test_whole_number(self):
        self.assertEqual(format_price(2.0), "2.00")

    def test_rounds_up_past_tie(self):
        self.assertEqual(format_price(3.456), "3.46")


class TestParsePrice(unittest.TestCase):
    def test_strips_symbol(self):
        self.assertEqual(parse_price("$4.20"), 4.2)


if __name__ == "__main__":
    unittest.main()
