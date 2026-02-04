#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from typing import Dict, Any, List, Optional
from pydantic import ValidationError
import json
import logging
import logging.config
import os
import random
import shutil
import sys
import asyncio
from pathlib import Path
from datetime import date, datetime, timedelta
from time import sleep

import aiohttp
from absl import app, flags
from tqdm import tqdm

from . import config_util, datetime_util
from .config import SpiderConfig
from .downloader import AvatarPictureDownloader, Downloader
from .parser import AlbumParser, IndexParser, PageParser, PhotoParser
from .parser.util import handle_html_async
from .user import User
from .writer import Writer

FLAGS = flags.FLAGS

flags.DEFINE_string('config_path', None, 'The path to config.json.')
flags.DEFINE_string('u', None, 'The user_id we want to input.')
flags.DEFINE_string('user_id_list', None, 'The path to user_id_list.txt.')
flags.DEFINE_string('output_dir', None, 'The dir path to store results.')

logging_path = Path(__file__).parent / 'logging.conf'
logging.config.fileConfig(logging_path)
logger = logging.getLogger('spider')


class Spider:
    def __init__(self, config: SpiderConfig) -> None:
        """Weibo类初始化"""
        self.config = config
        self.filter: int = config.filter
        since_date = config.since_date
        if isinstance(since_date, int):
            since_date = date.today() - timedelta(since_date)
        self.since_date: str = str(
            since_date)  # 起始时间，即爬取发布日期从该值到结束时间的微博，形式为yyyy-mm-dd
        self.end_date: str = str(config.end_date)  # 结束时间，即爬取发布日期从起始时间到该值的微博，形式为yyyy-mm-dd，特殊值"now"代表现在
        
        self.random_wait_pages: List[int] = [
            min(config.random_wait_pages),
            max(config.random_wait_pages)
        ]
        self.random_wait_seconds: List[int] = [
            min(config.random_wait_seconds),
            max(config.random_wait_seconds)
        ]
        self.global_wait: List[List[int]] = config.global_wait
        self.page_count: int = 0
        self.write_mode: List[str] = config.write_mode
        self.pic_download: int = config.pic_download
        self.video_download: int = config.video_download
        self.file_download_timeout: List[int] = config.file_download_timeout
        self.result_dir_name: int = config.result_dir_name
        self.cookie: str = config.cookie
        self.mysql_config: Optional[Dict[str, Any]] = config.mysql_config
        self.sqlite_config: Optional[str] = config.sqlite_config
        self.kafka_config: Optional[Dict[str, Any]] = config.kafka_config
        self.mongo_config: Optional[Dict[str, Any]] = config.mongo_config
        self.post_config: Optional[Dict[str, Any]] = config.post_config
        
        self.user_config_file_path: str = ''
        user_id_list = config.user_id_list
        if FLAGS.user_id_list:
            user_id_list = FLAGS.user_id_list
        
        if not isinstance(user_id_list, list):
            if not Path(user_id_list).is_absolute():
                user_id_list = str(Path.cwd() / user_id_list)
            if not Path(user_id_list).is_file():
                logger.warning(f'不存在{user_id_list}文件')
                sys.exit()
            self.user_config_file_path = user_id_list
        if FLAGS.u:
            user_id_list = FLAGS.u.split(',')
        if isinstance(user_id_list, list):
            # 第一部分是处理dict类型的
            # 第二部分是其他类型,其他类型提供去重功能
            user_config_list = list(
                map(
                    lambda x: {
                        'user_uri': x['id'],
                        'since_date': x.get('since_date', self.since_date),
                        'end_date': x.get('end_date', self.end_date),
                    }, [user_id for user_id in user_id_list
                        if isinstance(user_id, dict)])) + list(
                    map(
                        lambda x: {
                            'user_uri': x,
                            'since_date': self.since_date,
                            'end_date': self.end_date
                        },
                        set([
                            user_id for user_id in user_id_list
                            if not isinstance(user_id, dict)
                        ])))
            if FLAGS.u:
                config_util.add_user_uri_list(self.user_config_file_path,
                                              user_id_list)
        else:
            user_config_list = config_util.get_user_config_list(
                user_id_list, self.since_date)
            for user_config in user_config_list:
                user_config['end_date'] = self.end_date
        self.user_config_list: List[Dict[str, str]] = user_config_list  # 要爬取的微博用户的user_config列表
        self.user_config: Dict[str, str] = {}  # 用户配置,包含用户id和since_date
        self.new_since_date: str = ''  # 完成某用户爬取后，自动生成对应用户新的since_date
        self.user: User = User()  # 存储爬取到的用户信息
        self.got_num: int = 0  # 存储爬取到的微博数
        self.weibo_id_list: List[str] = []  # 存储爬取到的所有微博id
        self.session: Optional[aiohttp.ClientSession] = None # aiohttp session
        
        self.writers: List[Writer] = []
        self.downloaders: List[Downloader] = []

    async def write_weibo(self, weibos: List[Any]) -> None:
        """将爬取到的信息写入文件或数据库"""
        for downloader in self.downloaders:
            await downloader.download_files(weibos, self.session)
        for writer in self.writers:
            await writer.write_weibo(weibos)

    async def write_user(self, user: User) -> None:
        """将用户信息写入数据库"""
        for writer in self.writers:
            await writer.write_user(user)

    async def get_user_info(self, user_uri: str) -> None:
        """获取用户信息"""
        url = f'https://weibo.cn/{user_uri}/profile'
        selector = await handle_html_async(self.cookie, url, self.session)
        self.user = await IndexParser(self.cookie, user_uri, selector=selector).get_user_async(self.session)
        self.page_count += 1

    async def download_user_avatar(self, user_uri: str) -> None:
        """下载用户头像"""
        # Note: This remains synchronous for now as it's a minor part of the flow
        avatar_album_url = PhotoParser(self.cookie,
                                       user_uri).extract_avatar_album_url()
        pic_urls = AlbumParser(self.cookie,
                               avatar_album_url).extract_pic_urls()
        await AvatarPictureDownloader(
            self._get_filepath('img'),
            self.file_download_timeout).handle_download(pic_urls, self.session)

    async def get_weibo_info(self):
        """获取微博信息"""
        try:
            since_date = datetime_util.str_to_time(
                self.user_config['since_date'])
            now = datetime.now()
            if since_date <= now:
                # Async fetch page num
                user_uri = self.user_config['user_uri']
                url = f'https://weibo.cn/{user_uri}/profile'
                selector = await handle_html_async(self.cookie, url, self.session)
                page_num = IndexParser(self.cookie, user_uri, selector=selector).get_page_num()
                
                self.page_count += 1
                if self.page_count > 2 and (self.page_count +
                                            page_num) > self.global_wait[0][0]:
                    wait_seconds = int(
                        self.global_wait[0][1] *
                        min(1, self.page_count / self.global_wait[0][0]))
                    logger.info(f'即将进入全局等待时间，{wait_seconds}秒后程序继续执行')
                    for i in tqdm(range(wait_seconds)):
                        await asyncio.sleep(1)
                    self.page_count = 0
                    self.global_wait.append(self.global_wait.pop(0))
                page1 = 0
                random_pages = random.randint(*self.random_wait_pages)
                for page in tqdm(range(1, page_num + 1), desc='Progress'):
                    # Get URL from parser without fetching
                    parser_temp = PageParser(
                        self.cookie,
                        self.user_config, page, self.filter, defer_fetch=True)
                    
                    # Async fetch with retry
                    selector = None
                    for _ in range(3):
                        selector = await handle_html_async(self.cookie, parser_temp.url, self.session)
                        if selector is not None:
                             info = selector.xpath("//div[@class='c']")
                             if info and len(info) > 0:
                                 break
                    
                    parser = PageParser(self.cookie, self.user_config, page, self.filter, selector=selector)
                    
                    weibos, self.weibo_id_list, to_continue = parser.get_one_page(self.weibo_id_list)
                    
                    logger.info(
                        f"{'-' * 30}已获取{self.user.nickname}({self.user.id})的第{page}页微博{'-' * 30}"
                    )
                    self.page_count += 1
                    if weibos:
                        yield weibos
                    if not to_continue:
                        break

                    if (page - page1) % random_pages == 0 and page < page_num:
                        await asyncio.sleep(random.randint(*self.random_wait_seconds))
                        page1 = page
                        random_pages = random.randint(*self.random_wait_pages)

                    if self.page_count >= self.global_wait[0][0]:
                        logger.info(f'即将进入全局等待时间，{self.global_wait[0][1]}秒后程序继续执行')
                        for i in tqdm(range(self.global_wait[0][1])):
                            await asyncio.sleep(1)
                        self.page_count = 0
                        self.global_wait.append(self.global_wait.pop(0))

                if self.user_config_file_path or FLAGS.u:
                    config_util.update_user_config_file(
                        self.user_config_file_path,
                        self.user_config['user_uri'],
                        self.user.nickname,
                        self.new_since_date,
                    )
        except Exception as e:
            logger.exception(e)

    def _get_filepath(self, type: str) -> Path:
        """获取结果文件路径"""
        try:
            dir_name = self.user.nickname
            if self.result_dir_name:
                dir_name = self.user.id
            if FLAGS.output_dir is not None:
                file_dir = Path(FLAGS.output_dir) / dir_name
            else:
                file_dir = Path.cwd() / 'weibo' / dir_name
            if type == 'img' or type == 'video':
                file_dir = file_dir / type
            if not file_dir.is_dir():
                file_dir.mkdir(parents=True, exist_ok=True)
            if type == 'img' or type == 'video':
                return file_dir
            file_path = file_dir / f'{self.user.id}.{type}'
            return file_path
        except Exception as e:
            logger.exception(e)
            return Path() # Return empty path on error to match signature

    def initialize_info(self, user_config: Dict[str, str]) -> None:
        """初始化爬虫信息"""
        self.got_num = 0
        self.user_config = user_config
        self.weibo_id_list = []
        if self.end_date == 'now':
            self.new_since_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        else:
            self.new_since_date = self.end_date
        self.writers = []
        if 'csv' in self.write_mode:
            from .writer import CsvWriter

            self.writers.append(
                CsvWriter(self._get_filepath('csv'), self.filter))
        if 'txt' in self.write_mode:
            from .writer import TxtWriter

            self.writers.append(
                TxtWriter(self._get_filepath('txt'), self.filter))
        if 'json' in self.write_mode:
            from .writer import JsonWriter

            self.writers.append(JsonWriter(self._get_filepath('json')))
        if 'mysql' in self.write_mode:
            from .writer import MySqlWriter

            self.writers.append(MySqlWriter(self.mysql_config))
        if 'mongo' in self.write_mode:
            from .writer import MongoWriter

            self.writers.append(MongoWriter(self.mongo_config))
        if 'sqlite' in self.write_mode:
            from .writer import SqliteWriter

            self.writers.append(SqliteWriter(self.sqlite_config))

        if 'kafka' in self.write_mode:
            from .writer import KafkaWriter

            self.writers.append(KafkaWriter(self.kafka_config))

        if 'post' in self.write_mode:
            from .writer import PostWriter

            self.writers.append(PostWriter(self.post_config))

        self.downloaders = []
        if self.pic_download == 1:
            from .downloader import (
                OriginPictureDownloader,
                RetweetPictureDownloader)

            self.downloaders.append(
                OriginPictureDownloader(self._get_filepath('img'),
                                        self.file_download_timeout))
        if self.pic_download and not self.filter:
            self.downloaders.append(
                RetweetPictureDownloader(self._get_filepath('img'),
                                         self.file_download_timeout))
        if self.video_download == 1:
            from .downloader import VideoDownloader

            self.downloaders.append(
                VideoDownloader(self._get_filepath('video'),
                                self.file_download_timeout))

    async def get_one_user(self, user_config: Dict[str, str]) -> None:
        """获取一个用户的微博"""
        try:
            await self.get_user_info(user_config['user_uri'])
            logger.info(self.user)
            logger.info('*' * 100)

            self.initialize_info(user_config)
            await self.write_user(self.user)
            logger.info('*' * 100)

            # 下载用户头像相册中的图片。
            if self.pic_download:
                await self.download_user_avatar(user_config['user_uri'])

            async for weibos in self.get_weibo_info():
                await self.write_weibo(weibos)
                self.got_num += len(weibos)
            if not self.filter:
                logger.info(f'共爬取{self.got_num}条微博')
            else:
                logger.info(f'共爬取{self.got_num}条原创微博')
            logger.info('信息抓取完毕')
            logger.info('*' * 100)
        except Exception as e:
            logger.exception(e)

    async def start(self) -> None:
        """运行爬虫"""
        try:
            if not self.user_config_list:
                logger.info(
                    '没有配置有效的user_id，请通过config.json或user_id_list.txt配置user_id')
                return
            
            async with aiohttp.ClientSession() as session:
                self.session = session
                user_count = 0
                user_count1 = random.randint(*self.random_wait_pages)
                random_users = random.randint(*self.random_wait_pages)
                for user_config in self.user_config_list:
                    if (user_count - user_count1) % random_users == 0:
                        await asyncio.sleep(random.randint(*self.random_wait_seconds))
                        user_count1 = user_count
                        random_users = random.randint(*self.random_wait_pages)
                    user_count += 1
                    await self.get_one_user(user_config)
        except Exception as e:
            logger.exception(e)


def _get_config():
    """获取config.json数据"""
    src = Path(__file__).parent / 'config_sample.json'
    config_path = Path.cwd() / 'config.json'
    if FLAGS.config_path:
        config_path = Path(FLAGS.config_path)
    elif not config_path.is_file():
        shutil.copy(src, config_path)
        logger.info(f'请先配置当前目录({Path.cwd()})下的config.json文件，'
                    '如果想了解config.json参数的具体意义及配置方法，请访问\n'
                    'https://github.com/dataabc/weiboSpider#2程序设置')
        sys.exit()
    try:
        with open(config_path) as f:
            try:
                config_util.check_cookie(config_path)
            except Exception:
                logger.info("Using the cookie field in config.json as the request cookie.")
            config = json.loads(f.read())
            return config
    except ValueError:
        logger.error('config.json 格式不正确，请访问 '
                     'https://github.com/dataabc/weiboSpider#2程序设置')
        sys.exit()

async def async_main(_):
    try:
        config_dict = _get_config()
        config = SpiderConfig(**config_dict)
        wb = Spider(config)
        await wb.start()  # 爬取微博信息
    except ValidationError as e:
        logger.error(f"配置验证失败:\n{e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(e)

def main(_):
    asyncio.run(async_main(_))

if __name__ == '__main__':
    app.run(main)