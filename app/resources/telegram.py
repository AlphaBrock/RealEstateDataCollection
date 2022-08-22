# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     telegram.py
   Description :     推送消息到Telegram
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/5 12:34
-------------------------------------------------
"""

import requests
from loguru import logger

from app.common.settingReader import ConfigReader


class Alarm(ConfigReader):

    def __init__(self):
        super().__init__()
        self.tgBotToken = self.conf["Telegram"]["TgBotToken"]
        self.chatID = self.conf["Telegram"]["TgChatID"]

    def sendMsg(self, messages):
        logger.debug("sendMessages is: {}".format(messages))
        url = "https://api.telegram.org/bot{}/sendMessage".format(self.tgBotToken)
        params = {
            "chat_id": self.chatID,
            "text":  messages,
            "parse_mode": "markdown"
        }
        try:
            response = requests.request("GET", url, params=params, verify=False, timeout=20)
            logger.info(response.text)
        except Exception as e:
            logger.exception(str(e))