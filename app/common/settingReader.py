# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     settingReader.py
   Description :     读取配置文件
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/7/31 20:24
-------------------------------------------------
"""
import configparser
import os


class ConfigReader(object):

    def __init__(self):
        self.path = "config/config.ini"
        self.conf = configparser.ConfigParser()
        try:
            if os.path.exists(self.path):
                self.conf.read(self.path, encoding="utf-8")
        except IOError as e:
            raise e
