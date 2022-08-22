# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     monitor.py
   Description :     监控模块
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/17 18:00
-------------------------------------------------
"""
import datetime
import json
import random
import time
from ipaddress import IPv4Address

import requests
from loguru import logger
from app.common.settingReader import ConfigReader
from app.common.sqlite3 import dbSelect, dbExecute, dbExecuteMany
from app.common.utils import parseHtmls
from app.resources.telegram import Alarm as telegram
from app.resources.wework import Alarm as wework

telegram = telegram()
wework = wework()


class Monitor(ConfigReader):

    def __init__(self):
        super().__init__()

    def monitorIfNewHouseSaled(self, BuildingId):
        sql = 'SELECT PresaleDetailsInfoUrl,BuildingIds,BuildingNames FROM ProjectDetailData WHERE BuildingIds like "%{}%" '.format(BuildingId)
        result = dbSelect(sql)
        if len(result) == 0:
            logger.error("所输入的BuildingId:{}不存在, 不进行监控".format(BuildingId))
            return

        BuildingIds = result[0][1].split(",")
        BuildingNames = result[0][2].split(",")
        for i in range(0, len(BuildingIds)):
            if BuildingIds[i] == BuildingId:
                data = {
                    "BuildingId": BuildingId,
                    "BuildingName": BuildingNames[i],
                    "PresellDetailsInfoUrl": result[0][0]
                }
                logger.info("数据库查询内容:{}".format(json.dumps(data, ensure_ascii=False)))
                self.getRoomListInfo(data)

    def getRoomListInfo(self, data, **kwargs):
        try:
            url = "http://{}/HPMS/RoomList.aspx".format(self.conf["SPIDER"]["HOST"])
            params = {
                "code": data["BuildingId"],
                "rsr": 1000,
                "rse": 0,
                "rhx": 3000,
                "jzmj": "",
                "tnmj": ""
            }
            headers = {
                "User-Agent": self.conf["SPIDER"]["UserAgent"],
                "Referer": self.conf["SPIDER"]["Referer"] + "/" + data["PresellDetailsInfoUrl"],
                "Host": self.conf["SPIDER"]["Host"],
                "X-Forwarded-For": str(IPv4Address(random.getrandbits(32)))
            }
            if kwargs.get("cookie"):
                response = requests.request("GET", url=url, params=params, headers=headers, cookies=kwargs.get("cookie"), timeout=120)
            else:
                response = requests.request("GET", url=url, params=params, headers=headers, timeout=120)
            parseHtml = parseHtmls(response.text.replace('<ItemTemplate>','').replace('</ItemTemplate>', ''))

            insertData = []

            logger.info("房间数:{}".format(len(parseHtml.xpath('/html/body/form/div[3]/table/tr')[1:])))

            for i in range(2, len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr')[1:]) + 2):
                data["RoomNumber"] = parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/u/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/u/text()'.format(i))) > 0 else ""
                data["RoomInfoUrl"] = "/HPMS/" + parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/@href'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/@href'.format(i))) > 0 else ""
                data["RoomUse"] = parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[3]/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[3]/text()'.format(i))) > 0 else ""
                data["RoomTotalArea"] = float(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[4]/text()'.format(i))[0]) if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[4]/text()'.format(i))) > 0 else 0
                data["RoomInsideArea"] = float(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[5]/text()'.format(i))[0]) if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[5]/text()'.format(i))) > 0 else 0
                data["RoomSaleStatus"] = parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[6]/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[6]/text()'.format(i))) > 0 else ""
                data["RoomShareArea"] = round(data["RoomTotalArea"] - data["RoomInsideArea"], 2)
                data["Updatetime"] = str(datetime.datetime.fromtimestamp(int(time.time())))

                # 判断楼层房号是否销售
                fetchRowCnt = dbSelect('SELECT RoomSaleStatus FROM RoomDetailData WHERE BuildingId="{}" AND RoomNumber="{}"'.format(data["BuildingId"], data["RoomNumber"]))
                if len(fetchRowCnt) == 0:
                    logger.warning("当前房屋信息不存在数据库, BuildingId:{}, BuildingName:{}, RoomInfoUrl:{}, 需执行INSERT......".format(data["BuildingId"], data["BuildingName"], data["RoomInfoUrl"]))
                    insertData.append((data["BuildingId"], data["BuildingName"], data["RoomNumber"], data["RoomInfoUrl"], data["RoomUse"], data["RoomTotalArea"], data["RoomInsideArea"], data["RoomSaleStatus"], data["RoomShareArea"], data["Updatetime"]))
                else:
                    if fetchRowCnt[0][0] == data["RoomSaleStatus"]:
                        logger.warning("当前房屋信息存在数据库, 但销售状态未发生变更, BuildingId:{}, BuildingName:{}, RoomInfoUrl:{}, 无需UPDATE".format(data["BuildingId"], data["BuildingName"], data["RoomInfoUrl"]))
                    else:
                        logger.info("当前房屋信息存在数据库, 且销售状态发生变更, 原:{}, 现:{}, BuildingId:{}, BuildingName:{}, RoomInfoUrl:{}, 需执行UPDATE......".format(fetchRowCnt[0][0], data["RoomSaleStatus"], data["BuildingId"], data["BuildingName"], data["RoomInfoUrl"]))
                        self.getRoomDetailInfo(data, cookie=response.cookies)
                        dbExecute('UPDATE RoomDetailData SET RoomSaleStatus="{}", UpdateTime="{}" WHERE BuildingId="{}" AND RoomInfoUrl="{}"'.format(data["RoomSaleStatus"], data["Updatetime"], data["BuildingId"], data["RoomInfoUrl"]))
            if len(insertData) > 0:
                dbExecuteMany('INSERT INTO RoomDetailData(BuildingId, BuildingName, RoomNumber, RoomInfoUrl, RoomUse, RoomTotalArea, RoomInsideArea, RoomSaleStatus, RoomShareArea, UpdateTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', insertData)
        except Exception as e:
            logger.exception(str(e))

    def getRoomDetailInfo(self, data, **kwargs):
        global response
        text = []
        try:
            url = "http://" + self.conf["SPIDER"]["HOST"] + data["RoomInfoUrl"]
            headers = {
                "User-Agent": self.conf["SPIDER"]["UserAgent"],
                "Referer": self.conf["SPIDER"]["Referer"] + "/" + data["PresellDetailsInfoUrl"],
                "Host": self.conf["SPIDER"]["Host"],
                "X-Forwarded-For": str(IPv4Address(random.getrandbits(32)))
            }
            # 笨方法重试5次，还不行就放弃
            count = 0
            while count < 5:
                try:
                    if kwargs.get("cookie"):
                        response = requests.request("GET", url=url, headers=headers, cookies=kwargs.get("cookie"), timeout=30)
                    else:
                        response = requests.request("GET", url=url, headers=headers, timeout=30)
                    break
                except:
                    time.sleep(random.randint(1, 5))
                    count = count + 1
            parseHtml = parseHtmls(response.text)
            data["RoomFloorNumber"] = int(parseHtml.xpath('//*[@id="ROOM_MYC"]/text()')[0])
            data["RoomNature"] = parseHtml.xpath('//*[@id="ROOM_FWXZ"]/text()')[0]
            data["RoomType"] = parseHtml.xpath('//*[@id="ROOM_HX"]/text()')[0]
            data["RoomTotalPrice"] = float(parseHtml.xpath('//*[@id="ROOM_WJBAZJ"]/@value')[0]) if len(parseHtml.xpath('//*[@id="ROOM_WJBAZJ"]/@value')) > 0 else 0
            data["RoomUnitPrice"] = float(parseHtml.xpath('//*[@id="ROOM_WJBADJ"]/@value')[0]) if len(parseHtml.xpath('//*[@id="ROOM_WJBADJ"]/@value')) > 0 else 0
            data["RoomLocation"] = parseHtml.xpath('//*[@id="ROOM_FWZL"]/text()')[0]

            dbExecute('UPDATE RoomDetailData SET RoomType="{}", RoomFloorNumber={}, RoomNature="{}", RoomType="{}", RoomTotalPrice={}, RoomUnitPrice={}, RoomLocation="{}", UpdateTime="{}" WHERE BuildingId="{}" AND RoomNumber="{}"'.format(data["RoomType"], data["RoomFloorNumber"], data["RoomNature"], data["RoomType"], data["RoomTotalPrice"], data["RoomUnitPrice"], data["RoomLocation"], datetime.datetime.fromtimestamp(int(time.time())), data["BuildingId"], data["RoomNumber"]))

            ProjectName = dbSelect("SELECT ProjectName FROM ProjectDetailData WHERE BuildingIds LIKE '%{}%'".format(data["BuildingId"]))[0][0]
            text.append("项目名称:{}".format(ProjectName))
            text.append("建筑名称:{}".format(data["BuildingName"]))
            text.append("楼------层: {}".format(data["RoomFloorNumber"]))
            text.append("房------号: {}".format(data["RoomNumber"]))
            text.append("房屋性质:{}".format(data["RoomNature"]))
            text.append("房屋户型:{}".format(data["RoomType"]))
            text.append("建筑面积:{}㎡".format(data["RoomTotalArea"]))
            text.append("套内面积:{}㎡".format(data["RoomInsideArea"]))
            text.append("分摊面积:{}㎡".format(data["RoomShareArea"]))
            text.append("申报总价:{}元".format(data["RoomTotalPrice"]))
            text.append("申报单价:{}元".format(data["RoomUnitPrice"]))
            text.append("房屋坐落:{}".format(data["RoomLocation"]))
            template = "[中山房地产楼盘销售监控-新增备案房屋]👇\n\n" + "\n".join(text)
            logger.info("推送内容:{}".format(template))
            if len(self.conf["Telegram"]["TgBotToken"]) > 0:
                telegram.sendMsg(template)

            if len(self.conf["Wework"]["WECOM_CID"]) > 0:
                wework.sendMsg(template)

        except Exception as e:
            logger.exception(str(e))