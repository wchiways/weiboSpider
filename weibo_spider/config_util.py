import codecs
import logging
import browser_cookie3
from datetime import datetime
from pathlib import Path
import json
from .datetime_util import is_valid_date

logger = logging.getLogger('spider.config_util')


def get_user_config_list(file_name, default_since_date):
    """获取文件中的微博id信息"""
    import sys
    with open(file_name, 'rb') as f:
        try:
            lines = f.read().splitlines()
            lines = [line.decode('utf-8-sig') for line in lines]
        except UnicodeDecodeError:
            logger.error(f'{file_name}文件应为utf-8编码，请先将文件编码转为utf-8再运行程序')
            sys.exit()
        user_config_list = []
        for line in lines:
            info = line.split(' ')
            if len(info) > 0 and info[0].isdigit():
                user_config = {}
                user_config['user_uri'] = info[0]
                if len(info) > 2 and is_valid_date(info[2]):
                    if len(info) > 3 and is_valid_date(info[2] + ' ' + info[3]):
                        user_config['since_date'] = info[2] + ' ' + info[3]
                    else:
                        user_config['since_date'] = info[2]
                else:
                    user_config['since_date'] = default_since_date
                if user_config not in user_config_list:
                    user_config_list.append(user_config)
    return user_config_list


def update_user_config_file(user_config_file_path, user_uri, nickname,
                            start_time):
    """更新用户配置文件"""
    if not user_config_file_path:
        user_config_file_path = str(Path.cwd() / 'user_id_list.txt')
    with open(user_config_file_path, 'rb') as f:
        lines = f.read().splitlines()
        lines = [line.decode('utf-8-sig') for line in lines]
        for i, line in enumerate(lines):
            info = line.split(' ')
            if len(info) > 0:
                if user_uri == info[0]:
                    if len(info) == 1:
                        info.append(nickname)
                        info.append(start_time)
                    if len(info) == 2:
                        info.append(start_time)
                    if len(info) > 3 and is_valid_date(info[2] + ' ' + info[3]):
                        del info[3]
                    if len(info) > 2:
                        info[2] = start_time
                    lines[i] = ' '.join(info)
                    break
    with codecs.open(user_config_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def add_user_uri_list(user_config_file_path, user_uri_list):
    """向user_id_list.txt文件添加若干user_uri"""
    if not user_config_file_path:
        user_config_file_path = str(Path.cwd() / 'user_id_list.txt')
    if Path(user_config_file_path).is_file():
        user_uri_list[0] = '\n' + user_uri_list[0]
    with codecs.open(user_config_file_path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(user_uri_list))
      
def get_cookie():
    """Get weibo.cn cookie from Chrome browser"""
    try:
        chrome_cookies = browser_cookie3.chrome(domain_name='weibo.cn')
        cookies_dict = {cookie.name: cookie.value for cookie in chrome_cookies}
        return cookies_dict
    except Exception as e:
        logger.error(f'Failed to obtain weibo.cn cookie from Chrome browser: {e}')
        raise 
    
def update_cookie_config(cookie, user_config_file_path):
    """Update cookie in config.json"""
    if not user_config_file_path:
        user_config_file_path = str(Path.cwd() / 'config.json')
    try:
        with codecs.open(user_config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        cookie_string = '; '.join(f'{name}={value}' for name, value in cookie.items())
        
        if config['cookie'] != cookie_string:
            config['cookie'] = cookie_string
            with codecs.open(user_config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f'Failed to update cookie in config file: {e}')
        raise 
    
def check_cookie(user_config_file_path): 
    """Checks if user is logged in"""
    try:
        cookie = get_cookie()
        if cookie.get("MLOGIN", '0') == '0':
            logger.warning("使用 Chrome 在此登录 %s", "https://passport.weibo.com/sso/signin?entry=wapsso&source=wapssowb&url=https://m.weibo.cn/")
            sys.exit()
        else:
            update_cookie_config(cookie, user_config_file_path)
    except Exception as e:
        logger.error(f'Check for cookie failed: {e}')
        raise 
