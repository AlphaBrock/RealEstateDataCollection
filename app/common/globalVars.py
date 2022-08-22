# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     globalVars.py
   Description :     全局变量管理器
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/5 15:35
-------------------------------------------------
"""


def init():
    global globalDict
    globalDict = {}


def setValue(name, value):
    """
    定义一个全局变量
    :param name:
    :param value:
    :return:
    """
    globalDict[name] = value


def getValue(name, defValue=None):
    """
    获取一个全局变量值，不能存在则返回默认值
    :param name:
    :param defValue:
    :return:
    """
    try:
        return globalDict[name]
    except KeyError:
        return defValue
