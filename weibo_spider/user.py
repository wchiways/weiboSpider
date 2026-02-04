class User:
    __slots__ = (
        'id', 'nickname', 'gender', 'location', 'birthday', 'description',
        'verified_reason', 'talent', 'education', 'work', 'weibo_num',
        'following', 'followers'
    )

    def __init__(self):
        self.id = ''

        self.nickname = ''

        self.gender = ''
        self.location = ''
        self.birthday = ''
        self.description = ''
        self.verified_reason = ''
        self.talent = ''

        self.education = ''
        self.work = ''

        self.weibo_num = 0
        self.following = 0
        self.followers = 0

    def to_dict(self):
        """将对象转换为字典"""
        return {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot)}

    def __str__(self):
        """打印微博用户信息"""
        result = ''
        result += f'用户昵称: {self.nickname}\n'
        result += f'用户id: {self.id}\n'
        result += f'微博数: {self.weibo_num}\n'
        result += f'关注数: {self.following}\n'
        result += f'粉丝数: {self.followers}\n'
        return result
