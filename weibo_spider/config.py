from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pathlib import Path
from datetime import datetime
from .datetime_util import is_valid_date


class SpiderConfig(BaseModel):
    """微博爬虫配置类"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id_list: Union[List[Union[str, Dict[str, str]]], str] = Field(
        description="要爬取的微博用户ID列表，可以是ID列表，也可以是包含ID的字典列表，或txt文件路径。"
    )
    cookie: str = Field(description="微博的Cookie，用于身份验证。")
    filter: int = Field(default=0, description="过滤类型，0表示抓取全部微博，1表示只抓取原创微博。")
    since_date: Union[int, str] = Field(
        default=0, 
        description="抓取起始时间，形式为YYYY-MM-DD或YYYY-MM-DD HH:MM，或整数（表示从今天起的前n天）。"
    )
    end_date: str = Field(
        default="now", 
        description="抓取结束时间，形式为YYYY-MM-DD或YYYY-MM-DD HH:MM，或'now'表示当前时间。"
    )
    random_wait_pages: List[int] = Field(
        default_factory=lambda: [1, 5], 
        description="随机等待页数范围 [min, max]，每爬取多少页暂停一次。"
    )
    random_wait_seconds: List[int] = Field(
        default_factory=lambda: [6, 10], 
        description="随机等待时间范围 [min, max]（秒），每次暂停等待的时长。"
    )
    global_wait: List[List[int]] = Field(
        default_factory=lambda: [[1000, 3600]], 
        description="全局等待配置 [[页数, 秒数], ...]，例如每爬取1000页等待3600秒。"
    )
    write_mode: List[str] = Field(
        default_factory=lambda: ["csv"], 
        description="结果保存类型列表，可包含 'txt', 'csv', 'json', 'mongo', 'mysql', 'sqlite', 'kafka', 'post'。"
    )
    pic_download: int = Field(default=0, description="是否下载微博图片，0不下载，1下载。")
    video_download: int = Field(default=0, description="是否下载微博视频，0不下载，1下载。")
    file_download_timeout: List[int] = Field(
        default_factory=lambda: [5, 5, 10], 
        description="文件下载超时设置 [重试次数, 连接超时, 读取超时]。"
    )
    result_dir_name: int = Field(default=0, description="结果目录命名方式，0使用用户昵称，1使用用户ID。")
    mysql_config: Optional[Dict[str, Any]] = Field(default=None, description="MySQL数据库连接配置字典。")
    sqlite_config: Optional[str] = Field(default=None, description="SQLite数据库连接路径。")
    kafka_config: Optional[Dict[str, Any]] = Field(default=None, description="Kafka配置字典。")
    mongo_config: Optional[Dict[str, Any]] = Field(default=None, description="MongoDB配置字典。")
    post_config: Optional[Dict[str, Any]] = Field(default=None, description="POST请求配置字典（用于数据推送）。")

    @field_validator('filter', 'pic_download', 'video_download')
    @classmethod
    def check_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f'值应为0或1, 得到: {v}')
        return v

    @field_validator('since_date')
    @classmethod
    def check_since_date(cls, v: Union[int, str]) -> Union[int, str]:
        if isinstance(v, int):
            return v
        if not is_valid_date(str(v)):
            raise ValueError(f'since_date值应为yyyy-mm-dd形式或整数, 得到: {v}')
        return v

        @field_validator('end_date')

        @classmethod

        def check_end_date(cls, v: str) -> str:

            if v == 'now' or is_valid_date(v):

                return v

            raise ValueError(f'end_date值应为yyyy-mm-dd形式或"now",  得到: {v}')

    @field_validator('random_wait_pages', 'random_wait_seconds')
    @classmethod
    def check_wait_range(cls, v: List[int]) -> List[int]:
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError('参数值应为包含两个整数的list类型')
        if not all(isinstance(i, int) for i in v):
            raise ValueError('列表中的值应为整数类型')
        if min(v) < 1:
            raise ValueError('列表中的值应大于0')
        if v[0] > v[1]:
            raise ValueError('等待范围起始值不能大于结束值')
        return v

    @field_validator('global_wait')
    @classmethod
    def check_global_wait(cls, v: List[List[int]]) -> List[List[int]]:
        for g in v:
            if not isinstance(g, list) or len(g) != 2:
                raise ValueError('参数内的值应为长度为2的list类型')
            if not all(isinstance(i, int) and i >= 1 for i in g):
                raise ValueError('列表中的值应为大于0的整数')
        return v

    @field_validator('write_mode')
    @classmethod
    def check_write_mode(cls, v: List[str]) -> List[str]:
        valid_modes = {'txt', 'csv', 'json', 'mongo', 'mysql', 'sqlite', 'kafka', 'post'}
        for mode in v:
            if mode not in valid_modes:
                raise ValueError(f'{mode}为无效模式')
        return v

    @field_validator('user_id_list')
    @classmethod
    def check_user_id_list(cls, v: Union[List[Union[str, Dict[str, str]]], str]) -> Union[List[Union[str, Dict[str, str]]], str]:
        if isinstance(v, list):
            return v
        if not v.endswith('.txt'):
            raise ValueError('user_id_list值应为list类型或txt文件路径')
        
        path = Path(v)
        if not path.is_absolute():
            path = Path.cwd() / v
        if not path.is_file():
            raise ValueError(f'不存在{path}文件')
        return str(path)
