import unittest

from billing import blocks, invoice_amount


class TestBlocks(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(blocks(0), 0)

    def test_started_block_bills(self):
        self.assertEqual(blocks(1), 1)
        self.assertEqual(blocks(31), 2)

    def test_exact_multiples_close_the_block(self):
        self.assertEqual(blocks(30), 1)
        self.assertEqual(blocks(60), 2)


class TestInvoice(unittest.TestCase):
    def test_amount(self):
        self.assertEqual(invoice_amount(45, 50), 100)


if __name__ == "__main__":
    unittest.main()
