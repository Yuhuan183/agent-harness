import unittest

from bucketlog import count_by_day, day_bucket


class DayBucketTests(unittest.TestCase):
    def test_utc_account_keeps_utc_date(self):
        self.assertEqual(day_bucket(1772452800, 0), "2026-03-02")

    def test_midday_event_is_offset_safe(self):
        # 17:30Z at UTC-5 is 12:30 local, same calendar day.
        self.assertEqual(day_bucket(1772472600, -300), "2026-03-02")

    def test_counts_group_by_bucket(self):
        counts = count_by_day([1772452800, 1772472600], 0)
        self.assertEqual(counts, {"2026-03-02": 2})


if __name__ == "__main__":
    unittest.main()
