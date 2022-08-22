# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     utils.py
   Description :     奇奇怪怪的单独函数
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/5 17:26
-------------------------------------------------
"""
import hashlib
import time
import datetime
from lxml import etree
from loguru import logger


def md5(data):
    md5 = hashlib.md5()
    md5.update(data.encode(encoding='utf-8'))
    return md5.hexdigest()


def parseHtmls(html):
    """
        格式化html用以根據xpath獲取結果
        :param html:
        :return:
        """
    try:
        html = etree.HTML(html, etree.HTMLParser())
        return html
    except Exception as e:
        raise e


def loggers():
    return logger.add("log/RealEstatDataCollection.log", rotation="100 MB", retention='10 days', compression='zip', enqueue=True, level='INFO')
