import codecs
import json
import logging
import os
import asyncio
import aiohttp

from .writer import Writer

logger = logging.getLogger('spider.post_writer')

class PostWriter(Writer):
    def __init__(self, post_config):
        self.post_config = post_config
        self.api_url = post_config['api_url']
        self.api_token = post_config.get('api_token', None)
        self.dba_password = post_config.get('dba_password', None)

    async def write_user(self, user):
        self.user = user

    def _update_json_data(self, data, weibo_info):
        """将获取到的微博数据转换为json输出模式一致"""
        data['user'] = self.user.to_dict()
        if data.get('weibo'):
            data['weibo'] += weibo_info
        else:
            data['weibo'] = weibo_info
        return data

    async def send_post_request_with_token(self, url, data, token, max_retries, backoff_factor):
        headers = {
            'Content-Type': 'application/json',
            'api-token': f'{token}',
        }
        async with aiohttp.ClientSession() as session:
            for attempt in range(max_retries + 1):
                try:
                    async with session.post(url, json=data, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            # Continue to next attempt on non-200 status
                            if attempt < max_retries:
                                await asyncio.sleep(backoff_factor * (attempt + 1))
                                continue
                            logger.error(f"Unexpected response status: {response.status}")
                            return None
                except Exception as e:
                    if attempt < max_retries:
                        await asyncio.sleep(backoff_factor * (attempt + 1))  # 逐步增加等待时间，避免频繁重试
                        continue
                    else:
                        logger.error(f"在尝试{max_retries}次发出POST连接后，请求失败：{e}")

    async def write_weibo(self, weibos):
        """将爬到的信息POST到API"""
        data = {}
        data = self._update_json_data(data, [w.to_dict() for w in weibos])
        if data:
            await self.send_post_request_with_token(self.api_url, data, self.api_token, 3, 2)
            logger.info(f'{len(weibos)}条微博通过POST发送到 {self.api_url}')
        else:
            logger.info('没有获取到微博，略过API POST')
