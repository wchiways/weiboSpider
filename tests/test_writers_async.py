import unittest
import asyncio
import os
import shutil
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Mock aiofiles before importing modules that use it
sys.modules['aiofiles'] = MagicMock()

from weibo_spider.writer.txt_writer import TxtWriter
from weibo_spider.writer.csv_writer import CsvWriter
from weibo_spider.writer.json_writer import JsonWriter
from weibo_spider.user import User
from weibo_spider.weibo import Weibo

class TestWritersAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(
            id='123456',
            nickname='test_user',
            weibo_num=100,
            following=50,
            followers=200
        )
        self.weibo = Weibo(
            id='w1',
            user_id='123456',
            content='Test Weibo Content',
            publish_time='2023-01-01',
            up_num=10,
            retweet_num=5,
            comment_num=2
        )
        self.weibos = [self.weibo]

    @patch('weibo_spider.writer.txt_writer.aiofiles.open')
    async def test_txt_writer(self, mock_aio_open):
        file_path = 'test.txt'
        writer = TxtWriter(file_path, filter=0)
        
        mock_f = AsyncMock()
        mock_aio_open.return_value.__aenter__.return_value = mock_f
        
        await writer.write_user(self.user)
        mock_f.write.assert_called()
        
        await writer.write_weibo(self.weibos)
        mock_f.write.assert_called()

    @patch('weibo_spider.writer.csv_writer.aiofiles.open')
    async def test_csv_writer(self, mock_aio_open):
        file_path = 'test.csv'
        writer = CsvWriter(file_path, filter=0)
        
        mock_f = AsyncMock()
        mock_aio_open.return_value.__aenter__.return_value = mock_f
        
        await writer.write_weibo(self.weibos)
        mock_f.write.assert_called()
        # Verify content was written
        args, _ = mock_f.write.call_args
        self.assertIn('w1', args[0])
        self.assertIn('Test Weibo Content', args[0])

    @patch('weibo_spider.writer.json_writer.aiofiles.open')
    async def test_json_writer(self, mock_aio_open):
        file_path = 'test.json'
        writer = JsonWriter(file_path)
        
        mock_f = AsyncMock()
        mock_aio_open.return_value.__aenter__.return_value = mock_f
        # Mock read to return empty valid json
        mock_f.read.return_value = '{}'
        
        await writer.write_user(self.user)
        await writer.write_weibo(self.weibos)
        
        mock_f.write.assert_called()
        args, _ = mock_f.write.call_args
        self.assertIn('test_user', args[0])

if __name__ == '__main__':
    unittest.main()
