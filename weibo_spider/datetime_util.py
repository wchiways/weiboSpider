from datetime import datetime


def str_to_time(text: str) -> datetime:
    """将字符串转换成时间类型"""
    if ':' in text:
        result = datetime.strptime(text, '%Y-%m-%d %H:%M')
    else:
        result = datetime.strptime(text, '%Y-%m-%d')
    return result


def is_valid_date(date_str: str) -> bool:
    """判断日期格式是否正确"""
    try:
        str_to_time(date_str)
        return True
    except ValueError:
        return False
