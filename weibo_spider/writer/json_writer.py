import codecs
import json
import logging
from pathlib import Path
import aiofiles

from .writer import Writer

logger = logging.getLogger('spider.json_writer')


class JsonWriter(Writer):
    def __init__(self, file_path):
        self.file_path = file_path

    async def write_user(self, user):
        self.user = user

    def _update_json_data(self, data, weibo_info):
        """更新要写入json结果文件中的数据，已经存在于json中的信息更新为最新值，不存在的信息添加到data中"""
        data['user'] = self.user.to_dict()
        if data.get('weibo'):
            is_new = 1  # 待写入微博是否全部为新微博，即待写入微博与json中的数据不重复
            for old in data['weibo']:
                if weibo_info[-1]['id'] == old['id']:
                    is_new = 0
                    break
            if is_new == 0:
                for new in weibo_info:
                    flag = 1
                    for i, old in enumerate(data['weibo']):
                        if new['id'] == old['id']:
                            data['weibo'][i] = new
                            flag = 0
                            break
                    if flag:
                        data['weibo'].append(new)
            else:
                data['weibo'] += weibo_info
        else:
            data['weibo'] = weibo_info
        return data

    async def write_weibo(self, weibos):
        """将爬到的信息写入json文件"""
        data = {}
        if Path(self.file_path).is_file():
            async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                if content:
                    data = json.loads(content)
        
        data = self._update_json_data(data, [w.to_dict() for w in weibos])
        
        async with aiofiles.open(self.file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))
        logger.info(f'{len(weibos)}条微博写入json文件完毕，保存路径：{self.file_path}')
