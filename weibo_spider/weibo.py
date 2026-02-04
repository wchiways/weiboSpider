class Weibo:
    __slots__ = (
        'id', 'user_id', 'content', 'article_url', 'original_pictures',
        'retweet_pictures', 'original', 'video_url', 'original_pictures_list',
        'retweet_pictures_list', 'media', 'publish_place', 'publish_time',
        'publish_tool', 'up_num', 'retweet_num', 'comment_num'
    )

    def to_dict(self):
        """将对象转换为字典"""
        return {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot)}

    def __init__(self):
        self.id = ''
        self.user_id = ''
        self.content = ''
        self.article_url = ''
        self.original_pictures = []
        self.retweet_pictures = []
        self.original = True
        self.video_url = ''
        self.original_pictures_list = []
        self.retweet_pictures_list = []
        self.media = {}
        self.publish_place = ''
        self.publish_time = ''
        self.publish_tool = ''
        self.up_num = 0
        self.retweet_num = 0
        self.comment_num = 0

    def __str__(self):
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
