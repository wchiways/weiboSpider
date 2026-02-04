import unittest
from pydantic import ValidationError
from weibo_spider.config import SpiderConfig

class TestSpiderConfig(unittest.TestCase):
    def setUp(self):
        self.base_config = {
            'user_id_list': ['123456'],
            'cookie': 'test_cookie',
            'filter': 0,
            'since_date': '2023-01-01',
            'end_date': 'now',
            'write_mode': ['csv']
        }

    def test_valid_config(self):
        config = SpiderConfig(**self.base_config)
        self.assertEqual(config.user_id_list, ['123456'])
        self.assertEqual(config.filter, 0)

    def test_invalid_filter(self):
        config = self.base_config.copy()
        config['filter'] = 2  # Invalid
        with self.assertRaises(ValidationError):
            SpiderConfig(**config)

    def test_invalid_date(self):
        config = self.base_config.copy()
        config['since_date'] = 'invalid-date'
        with self.assertRaises(ValidationError):
            SpiderConfig(**config)

    def test_invalid_write_mode(self):
        config = self.base_config.copy()
        config['write_mode'] = ['invalid_mode']
        with self.assertRaises(ValidationError):
            SpiderConfig(**config)
            
    def test_wait_ranges(self):
        config = self.base_config.copy()
        # Test start > end
        config['random_wait_pages'] = [5, 1]
        with self.assertRaises(ValidationError) as cm:
            SpiderConfig(**config)
        self.assertIn('等待范围起始值不能大于结束值', str(cm.exception))

        # Test negative values
        config['random_wait_pages'] = [-1, 5]
        with self.assertRaises(ValidationError):
            SpiderConfig(**config)

if __name__ == '__main__':
    unittest.main()
