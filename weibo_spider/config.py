from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
from .config_util import validate_config

@dataclass
class SpiderConfig:
    """微博爬虫配置类

    Attributes:
        user_id_list: 要爬取的微博用户ID列表，可以是ID列表，也可以是包含ID的字典列表，或txt文件路径。
        cookie: 微博的Cookie，用于身份验证。
        filter: 过滤类型，0表示抓取全部微博，1表示只抓取原创微博。
        since_date: 抓取起始时间，形式为YYYY-MM-DD或YYYY-MM-DD HH:MM，或整数（表示从今天起的前n天）。
        end_date: 抓取结束时间，形式为YYYY-MM-DD或YYYY-MM-DD HH:MM，或"now"表示当前时间。
        random_wait_pages: 随机等待页数范围 [min, max]，每爬取多少页暂停一次。
        random_wait_seconds: 随机等待时间范围 [min, max]（秒），每次暂停等待的时长。
        global_wait: 全局等待配置 [[页数, 秒数], ...]，例如每爬取1000页等待3600秒。
        write_mode: 结果保存类型列表，可包含 "txt", "csv", "json", "mongo", "mysql", "sqlite", "kafka", "post"。
        pic_download: 是否下载微博图片，0不下载，1下载。
        video_download: 是否下载微博视频，0不下载，1下载。
        file_download_timeout: 文件下载超时设置 [重试次数, 连接超时, 读取超时]。
        result_dir_name: 结果目录命名方式，0使用用户昵称，1使用用户ID。
        mysql_config: MySQL数据库连接配置字典。
        sqlite_config: SQLite数据库连接路径。
        kafka_config: Kafka配置字典。
        mongo_config: MongoDB配置字典。
        post_config: POST请求配置字典（用于数据推送）。
    """
    user_id_list: Union[List[Union[str, Dict[str, str]]], str]
    cookie: str
    filter: int = 0
    since_date: Union[int, str] = 0
    end_date: str = "now"
    random_wait_pages: List[int] = field(default_factory=lambda: [1, 5])
    random_wait_seconds: List[int] = field(default_factory=lambda: [6, 10])
    global_wait: List[List[int]] = field(default_factory=lambda: [[1000, 3600]])
    write_mode: List[str] = field(default_factory=lambda: ["csv"])
    pic_download: int = 0
    video_download: int = 0
    file_download_timeout: List[int] = field(default_factory=lambda: [5, 5, 10])
    result_dir_name: int = 0
    mysql_config: Optional[Dict[str, Any]] = None
    sqlite_config: Optional[str] = None
    kafka_config: Optional[Dict[str, Any]] = None
    mongo_config: Optional[Dict[str, Any]] = None
    post_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后的验证逻辑"""
        # 使用现有的 validate_config 函数进行校验
        # 将 dataclass 转换为字典以适配旧有的验证函数
        config_dict = self.__dict__
        validate_config(config_dict)