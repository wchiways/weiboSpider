from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any

@dataclass(slots=True)
class Weibo:
    id: str = ''
    user_id: str = ''
    content: str = ''
    article_url: str = ''
    original_pictures: str = '' # Usually a string of URLs separated by comma or '无'
    retweet_pictures: str = '' # Usually a string of URLs separated by comma or '无'
    original: bool = True
    video_url: str = ''
    original_pictures_list: List[str] = field(default_factory=list)
    retweet_pictures_list: List[str] = field(default_factory=list)
    media: Dict[str, Any] = field(default_factory=dict) # Assuming media can be complex
    publish_place: str = ''
    publish_time: str = ''
    publish_tool: str = ''
    up_num: int = 0
    retweet_num: int = 0
    comment_num: int = 0

    def to_dict(self) -> dict:
        """将对象转换为字典"""
        return asdict(self)

    def __str__(self) -> str:
        """打印一条微博"""
        result = self.content + '\n'
        result += f'微博发布位置：{self.publish_place}\n'
        result += f'发布时间：{self.publish_time}\n'
        result += f'发布工具：{self.publish_tool}\n'
        result += f'点赞数：{self.up_num}\n'
        result += f'转发数：{self.retweet_num}\n'
        result += f'评论数：{self.comment_num}\n'
        result += f'url：https://weibo.cn/comment/{self.id}\n'
        return result
