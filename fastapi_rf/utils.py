import datetime
import inspect
import socket

import numpy as np


def _fix_datetime(t):
    t += datetime.timedelta(hours=8)
    t = f"{t:%Y-%m-%d %H:%M:%S}"
    return t


def format_datetime_into_isoformat(date_time: datetime.datetime) -> str:
    return _fix_datetime(date_time)


def return_type(func: callable):
    return inspect.signature(func).return_annotation

import json
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            print("MyEncoder-datetime.datetime")
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        if isinstance(obj, int):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
           return obj.tolist()
        elif isinstance(obj, np.integer):
           return int(obj)
        else:
            return super(MyEncoder, self).default(obj)

def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip

