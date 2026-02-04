# -*- coding: UTF-8 -*-
import asyncio
import logging
import sys
import random
from abc import ABC, abstractmethod
from pathlib import Path

import aiohttp
from tqdm import tqdm

logger = logging.getLogger('spider.downloader')


class Downloader(ABC):
    def __init__(self, file_dir, file_download_timeout):
        self.file_dir = Path(file_dir)
        self.describe = ''
        self.key = ''
        self.file_download_timeout = [5, 5, 10]
        if (isinstance(file_download_timeout, list)
                and len(file_download_timeout) == 3):
            for i in range(3):
                v = file_download_timeout[i]
                if isinstance(v, (int, float)) and v > 0:
                    self.file_download_timeout[i] = v

    @abstractmethod
    async def handle_download(self, urls, w, session):
        """下载 urls 里所指向的图片或视频文件，使用 w 里的信息来生成文件名"""
        pass

    async def download_one_file(self, url, file_path, weibo_id, session):
        """下载单个文件(图片/视频)"""
        try:
            file_path = Path(file_path)
            if not file_path.is_file():
                # 随机延时，模拟人工操作
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Retry logic
                retries = self.file_download_timeout[0]
                timeout = aiohttp.ClientTimeout(
                    connect=self.file_download_timeout[1],
                    total=self.file_download_timeout[2]
                )
                
                last_exception = None
                for _ in range(retries + 1):
                    try:
                        async with session.get(url, timeout=timeout) as response:
                            if response.status == 200:
                                content = await response.read()
                                with open(file_path, 'wb') as f:
                                    f.write(content)
                                break
                    except Exception as e:
                        last_exception = e
                else:
                    if last_exception:
                        raise last_exception

            return file_path.is_file()
        except Exception as e:
            error_file = self.file_dir / 'not_downloaded.txt'
            with open(error_file, 'ab') as f:
                url = f'{weibo_id}:{file_path}:{url}\n'
                f.write(url.encode(sys.stdout.encoding))
            logger.exception(e)
            return False

    async def download_files(self, weibos, session):
        """下载文件(图片/视频)"""
        try:
            logger.info(f'即将进行{self.describe}下载')
            for w in tqdm(weibos, desc='Download progress'):
                if getattr(w, self.key) != '无':
                    await self.handle_download(getattr(w, self.key), w, session)
            logger.info(f'{self.describe}下载完毕,保存路径:')
            logger.info(self.file_dir)
        except Exception as e:
            logger.exception(e)
