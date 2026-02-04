from dataclasses import dataclass, asdict

@dataclass(slots=True)
class User:
    id: str = ''
    nickname: str = ''
    gender: str = ''
    location: str = ''
    birthday: str = ''
    description: str = ''
    verified_reason: str = ''
    talent: str = ''
    education: str = ''
    work: str = ''
    weibo_num: int = 0
    following: int = 0
    followers: int = 0

    def to_dict(self) -> dict:
        """将对象转换为字典"""
        return asdict(self)

    def __str__(self) -> str:
        """打印微博用户信息"""
        result = ''
        result += f'用户昵称: {self.nickname}\n'
        result += f'用户id: {self.id}\n'
        result += f'微博数: {self.weibo_num}\n'
        result += f'关注数: {self.following}\n'
        result += f'粉丝数: {self.followers}\n'
        return result
