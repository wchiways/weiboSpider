import unittest
from unittest.mock import MagicMock, patch
from weibo_spider.spider import Spider
from weibo_spider.config import SpiderConfig

class TestSpiderInit(unittest.TestCase):
    @patch('weibo_spider.spider.FLAGS')
    def test_init(self, mock_flags):
        # Mock flags
        mock_flags.user_id_list = None
        mock_flags.u = None
        mock_flags.output_dir = None

        config_dict = {
            'user_id_list': ['123'],
            'filter': 1,
            'since_date': '2023-01-01',
            'write_mode': ['csv'],
            'cookie': 'cookie'
        }
        config = SpiderConfig(**config_dict)
        spider = Spider(config)
        self.assertEqual(spider.filter, 1)
        self.assertEqual(spider.since_date, '2023-01-01')
        self.assertIsInstance(spider.config, SpiderConfig)

if __name__ == '__main__':
    unittest.main()
