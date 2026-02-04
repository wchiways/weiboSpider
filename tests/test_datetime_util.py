import unittest
from datetime import datetime
from weibo_spider.datetime_util import str_to_time, is_valid_date

class TestDatetimeUtil(unittest.TestCase):
    def test_str_to_time(self):
        # Test YYYY-MM-DD
        dt1 = str_to_time('2023-01-01')
        self.assertEqual(dt1, datetime(2023, 1, 1))
        
        # Test YYYY-MM-DD HH:MM
        dt2 = str_to_time('2023-01-01 12:30')
        self.assertEqual(dt2, datetime(2023, 1, 1, 12, 30))
        
        # Test invalid format (should raise ValueError)
        with self.assertRaises(ValueError):
            str_to_time('invalid-date')

    def test_is_valid_date(self):
        self.assertTrue(is_valid_date('2023-01-01'))
        self.assertTrue(is_valid_date('2023-01-01 12:30'))
        self.assertFalse(is_valid_date('invalid-date'))
        self.assertFalse(is_valid_date('2023/01/01'))  # Wrong separator
