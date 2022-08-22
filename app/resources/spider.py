# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     spider.py
   Description :     
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/7/31 21:56
-------------------------------------------------
"""
import datetime
import json
import random
import threading
import time
from ipaddress import IPv4Address

import requests
from loguru import logger
import app.common.globalVars as globalVars
from app.common.settingReader import ConfigReader
from app.common.sqlite3 import dbExecute, dbSelect, dbExecuteMany
from app.common.threadLock import acquire
from app.common.utils import parseHtmls

mutex = threading.Lock()


class Spider(ConfigReader):

    def __init__(self):
        super().__init__()

    def pageListHtmlDownloader(self, HttpMethod, **kwargs):
        """
        下载房源总览清单网页内容
        :param HttpMethod:
        :param kwargs:
        :return:
        """
        Url = self.conf["DEFAULT"]["URL"]
        Headers = {
            "Referer": self.conf["DEFAULT"]["URL"],
            "User-Agent": self.conf["SPIDER"]["UserAgent"],
            "Host": self.conf["SPIDER"]["Host"],
            "Origin": self.conf["SPIDER"]["Origin"],
            "X-Forwarded-For": str(IPv4Address(random.getrandbits(32)))
        }
        if kwargs.get("Payload"):
            Headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = requests.request(HttpMethod, Url, headers=Headers, data=kwargs.get("Payload"), timeout=120)
        else:
            response = requests.request(HttpMethod, Url, headers=Headers, timeout=20)
        if response.status_code != 200:
            logger.debug(response.text)
        return response.text

    def getPageNum(self):
        """
        单纯的拿一个页数
        :return:
        """
        resultHtml = self.pageListHtmlDownloader(HttpMethod="GET")
        parseHtml = parseHtmls(resultHtml)
        pageNum = parseHtml.xpath('//*[@id="PageNavigator1_LblPageCount"]/text()')[0]
        VIEWSTATE = parseHtml.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
        VIEWSTATEGENERATOR = parseHtml.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]
        EVENTVALIDATION = parseHtml.xpath('//*[@id="__EVENTVALIDATION"]/@value')[0]

        with acquire(mutex):
            globalVars.setValue("VIEWSTATE", VIEWSTATE)
            globalVars.setValue("VIEWSTATEGENERATOR", VIEWSTATEGENERATOR)
            globalVars.setValue("EVENTVALIDATION", EVENTVALIDATION)
        dbExecute('INSERT INTO ProjectOverviewPageKey("ViewState", "ViewStateGenerator", "EventValidation") VALUES ("{}", "{}", "{}")'.format(VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION))
        return int(pageNum)

    async def pageListHtmlFindValue(self, pageNum, VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION):
        """
        根据下载的房源总览清单获取必须的结果进入下一步，一般从第二页开始，因为第一页已经获取了部分内容
        :param pageNum:
        :return:
        """
        try:
            Payload = {
                    "__EVENTTARGET": "PageNavigator1$LnkBtnNext",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": VIEWSTATE,
                    "__VIEWSTATEGENERATOR": VIEWSTATEGENERATOR,
                    "__EVENTVALIDATION": EVENTVALIDATION,
                    "txtXMMC": "",
                    "txtXkzh": "",
                    "txtKFQY": "",
                    "txtXMDZ": "",
                    "dpSZQY": "",
                    "txtQSTime": "",
                    "txtZZTime": "",
                    "PageNavigator1%24txtNewPageIndex": pageNum
                }

            resultHtml = self.pageListHtmlDownloader(HttpMethod="POST", Payload=Payload)
            parseHtml = parseHtmls(resultHtml)
            VIEWSTATE = parseHtml.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
            VIEWSTATEGENERATOR = parseHtml.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]
            EVENTVALIDATION = parseHtml.xpath('//*[@id="__EVENTVALIDATION"]/@value')[0]
            logger.info("pageNum:{}".format(pageNum))

            with acquire(mutex):
                globalVars.setValue("VIEWSTATE", VIEWSTATE)
                globalVars.setValue("VIEWSTATEGENERATOR", VIEWSTATEGENERATOR)
                globalVars.setValue("EVENTVALIDATION", EVENTVALIDATION)

            dbExecute('INSERT INTO ProjectOverviewPageKey(ViewState, ViewStateGenerator, EventValidation) VALUES ("{}", "{}", "{}")'.format(VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION))
            await self.getPresaleDetailsInfoUrl(parseHtml)
        except Exception as e:
            logger.exception(str(e))

    async def getPresaleDetailsInfoUrl(self, parseHtml):
        totalPresaleData = []
        updateData = []
        insertData = []
        for i in range(2, len(parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr')[1:]) + 2):
            data = {}
            data["PresellDetailsInfoUrl"] = "/" + parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[2]/a/@href'.format(i))[0] if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[2]/a/@href'.format(i))) > 0 else ""
            data["PermitNumber"] = parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[2]/a/u/text()'.format(i))[0] if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[2]/a/u/text()'.format(i))) > 0 else ""
            data["DevelopmentEnterprise"] = parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[3]/text()'.format(i))[0] if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[3]/text()'.format(i))) > 0 else ""
            data["ProjectName"] = parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[4]/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[4]/text()'.format(i))) > 0 else ""
            data["ProjectAddress"] = parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[5]/text()'.format(i))[0] if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[5]/text()'.format(i))) > 0 else ""
            data["TimeToMarket"] = parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[6]/text()'.format(i))[0] if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[6]/text()'.format(i))) > 0 else ""
            data["AreaLocation"] = parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[7]/text()'.format(i))[0] if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[7]/text()'.format(i))) > 0 else parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[7]/text()'.format(i))
            data["TotalNumber"] = int(parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[8]/text()'.format(i))[0]) if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[8]/text()'.format(i))) > 0 else ""
            data["AvailableNumber"] = int(parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[9]/text()'.format(i))[0]) if len(
                parseHtml.xpath('//*[@id="wrapper"]/div[3]/div/div[2]/table/tr[{}]/td[9]/text()'.format(i))) > 0 else ""

            data["Updatetime"] = datetime.datetime.fromtimestamp(int(time.time()))

            fetchRowCnt = dbSelect('SELECT PresaleDetailsInfoUrl,AvailableNumber FROM ProjectDetailData WHERE PresaleDetailsInfoUrl="{}"'.format(data["PresellDetailsInfoUrl"]))
            if len(fetchRowCnt) == 0:
                logger.warning("当前楼盘信息不存在数据库, URL:{}, 需执行INSERT......".format(data["PresellDetailsInfoUrl"]))
                insertData.append((data["PresellDetailsInfoUrl"], data["PermitNumber"], data["DevelopmentEnterprise"], data["ProjectName"], data["ProjectAddress"], data["TimeToMarket"], data["AreaLocation"], data["TotalNumber"], data["AvailableNumber"], data["Updatetime"]))
            else:
                if fetchRowCnt[0][1] != data["AvailableNumber"]:
                    logger.info("当前楼盘信息存在数据库, URL:{}, 需执行UPDATE......".format(data["PresellDetailsInfoUrl"]))
                    updateData.append((data["PresellDetailsInfoUrl"], data["AvailableNumber"]))

        if len(insertData) > 0:
            logger.info("当前有{}条数据需要执行INSERT".format(len(insertData)))
            dbExecuteMany('INSERT INTO ProjectDetailData(PresaleDetailsInfoUrl, PermitNumber, DevelopmentEnterprise, ProjectName, ProjectAddress, TimeToMarket, AreaLocation, TotalNumber, AvailableNumber, UpdateTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', insertData)

        if len(updateData) > 0:
            logger.info("当前有{}条数据需要执行UPDATE".format(len(updateData)))
            for i in updateData:
                dbExecute('UPDATE ProjectDetailData SET AvailableNumber="{}", UpdateTime="{}" WHERE PresaleDetailsInfoUrl="{}"'.format(i[1], datetime.datetime.fromtimestamp(int(time.time())), i[0]))

    def getPresaleInfo(self, data):
        try:
            url = "http://" + self.conf["SPIDER"]["Host"] + data.get("PresellDetailsInfoUrl")
            headers = {
                "User-Agent": self.conf["SPIDER"]["UserAgent"],
                "Referer": self.conf["DEFAULT"]["URL"],
                "Host": self.conf["SPIDER"]["Host"],
                "X-Forwarded-For": str(IPv4Address(random.getrandbits(32)))
            }
            response = requests.request("GET", url=url, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.warning(response.text)

            parseHtml = parseHtmls(response.text)
            data["PresaleCertificateNumber"] = parseHtml.xpath('//*[@id="Presel_XKZH"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_XKZH"]/text()')) > 0 else ""
            data["DateOfCertificate"] = parseHtml.xpath('//*[@id="Presel_FZRQ"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_FZRQ"]/text()')) > 0 else ""
            data["CertificateValidFrom"] = parseHtml.xpath('//*[@id="Presel_YXQX1"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_YXQX1"]/text()')) > 0 else ""
            data["CertificateExpiryDate"] = parseHtml.xpath('//*[@id="Presel_YXQX2"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_YXQX2"]/text()')) > 0 else ""
            data["CertificateAuthority"] = parseHtml.xpath('//*[@id="Presel_FZJG"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_FZJG"]/text()')) > 0 else ""
            data["PresaleFundsDepositBank"] = parseHtml.xpath('//*[@id="Presel_YSZJKHYH"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_YSZJKHYH"]/text()')) > 0 else ""
            data["PresaleFundsSupervisionAccount"] = parseHtml.xpath('//*[@id="Presel_YSZJZH"]/text()')[0] if len(parseHtml.xpath('//*[@id="Presel_YSZJZH"]/text()')) > 0 else ""
            data["ApprovedPresaleUnits"] = int(parseHtml.xpath('//*[@id="lblHZYSZTS"]/text()')[0]) if len(parseHtml.xpath('//*[@id="lblHZYSZTS"]/text()')) > 0 else ""
            data["ApprovedPresaleArea"] = int(parseHtml.xpath('//*[@id="lblHZYSZMJ"]/text()')[0]) if len(parseHtml.xpath('//*[@id="lblHZYSZMJ"]/text()')) > 0 else ""
            data["TotalSoldUnits"] = int(parseHtml.xpath('//*[@id="lblYSZTS"]/text()')[0]) if len(parseHtml.xpath('//*[@id="lblYSZTS"]/text()')) > 0 else ""
            data["TotalUnsoldUnits"] = int(parseHtml.xpath('//*[@id="lblWSZTS"]/text()')[0]) if len(parseHtml.xpath('//*[@id="lblWSZTS"]/text()')) > 0 else ""
            data["TotalSoldArea"] = int(parseHtml.xpath('//*[@id="lblYSZMJ"]/text()')[0]) if len(parseHtml.xpath('//*[@id="lblYSZMJ"]/text()')) > 0 else ""
            data["TotalUnsoldArea"] = int(parseHtml.xpath('//*[@id="lblWSZMJ"]/text()')[0]) if len(parseHtml.xpath('//*[@id="lblWSZMJ"]/text()')) > 0 else ""
            data["LandCertificateNumber"] = parseHtml.xpath('//*[@id="lblTDZH"]/text()')[0] if len(parseHtml.xpath('//*[@id="lblTDZH"]/text()')) > 0 else ""

            data["TotalBuildingNum"] = len(parseHtml.xpath('/html/body/form/div[3]/div/div[3]/div[2]/div[2]/input'))

            BuildingIds = []
            BuildingNames = []
            if data["TotalBuildingNum"] == 1:
                data["BuildingId"] = parseHtml.xpath('/html/body/form/div[3]/div/div[3]/div[2]/div[2]/input/@bid')[0]
                data["BuildingName"] = parseHtml.xpath('/html/body/form/div[3]/div/div[3]/div[2]/div[2]/span/text()')[0]
                BuildingIds.append(data["BuildingId"])
                BuildingNames.append(data["BuildingName"])
                self.getRoomListInfo(data, cookie=response.cookies)
            else:
                for i in range(1, data["TotalBuildingNum"] + 1):
                    data["BuildingId"] = parseHtml.xpath('/html/body/form/div[3]/div/div[3]/div[2]/div[2]/input[{}]/@bid'.format(i))[0]
                    data["BuildingName"] = parseHtml.xpath('/html/body/form/div[3]/div/div[3]/div[2]/div[2]/span[{}]/text()'.format(i))[0]
                    BuildingIds.append(data["BuildingId"])
                    BuildingNames.append(data["BuildingName"])
                    self.getRoomListInfo(data, cookie=response.cookies)

            logger.info("更新ProjectDetailData表, 当前BuildingIds:{}, BuildingNames:{}".format(",".join(BuildingIds), ",".join(BuildingNames)))
            dbExecute('UPDATE ProjectDetailData SET PresaleCertificateNumber="{}", DateOfCertificate="{}", CertificateValidFrom="{}", CertificateExpiryDate="{}", CertificateAuthority="{}", PresaleFundsDepositBank="{}", PresaleFundsSupervisionAccount="{}", ApprovedPresaleUnits={}, ApprovedPresaleArea={}, TotalSoldUnits={}, TotalUnsoldUnits={}, TotalSoldArea={}, TotalUnsoldArea={}, LandCertificateNumber="{}", BuildingIds="{}", BuildingNames="{}", UpdateTime="{}" WHERE PresaleDetailsInfoUrl="{}"'.format(data["PresaleCertificateNumber"], data["DateOfCertificate"], data["CertificateValidFrom"], data["CertificateExpiryDate"], data["CertificateAuthority"], data["PresaleFundsDepositBank"], data["PresaleFundsSupervisionAccount"], data["ApprovedPresaleUnits"], data["ApprovedPresaleArea"], data["TotalSoldUnits"], data["TotalUnsoldUnits"], data["TotalSoldArea"], data["TotalUnsoldArea"], data["LandCertificateNumber"], ",".join(BuildingIds), ",".join(BuildingNames), datetime.datetime.fromtimestamp(int(time.time())), data.get("PresellDetailsInfoUrl")))
        except Exception as e:
            logger.exception(str(e))
        finally:
            del data["TotalBuildingNum"]

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
            data["DataType"] = "getRoomListInfo"
            insertData = []
            for i in range(2, len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr')[1:]) + 2):
                data["RoomNumber"] = parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/u/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/u/text()'.format(i))) > 0 else ""
                data["RoomInfoUrl"] = "/HPMS/" + parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/@href'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[1]/a/@href'.format(i))) > 0 else ""
                data["RoomUse"] = parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[3]/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[3]/text()'.format(i))) > 0 else ""
                data["RoomTotalArea"] = float(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[4]/text()'.format(i))[0]) if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[4]/text()'.format(i))) > 0 else 0
                data["RoomInsideArea"] = float(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[5]/text()'.format(i))[0]) if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[5]/text()'.format(i))) > 0 else 0
                data["RoomSaleStatus"] = parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[6]/text()'.format(i))[0] if len(parseHtml.xpath('//*[@id="divRoomList"]/table/tr[{}]/td[6]/text()'.format(i))) > 0 else ""
                data["RoomShareArea"] = round(data["RoomTotalArea"] - data["RoomInsideArea"], 2)
                data["Updatetime"] = str(datetime.datetime.fromtimestamp(int(time.time())))

                fetchRowCnt = dbSelect('SELECT RoomSaleStatus FROM RoomDetailData WHERE BuildingId="{}" AND RoomNumber="{}"'.format(data["BuildingId"], data["RoomNumber"]))
                if len(fetchRowCnt) == 0:
                    logger.warning("当前房屋信息不存在数据库, BuildingId:{}, BuildingName:{}, RoomInfoUrl:{}, 需执行INSERT......".format(data["BuildingId"], data["BuildingName"], data["RoomInfoUrl"]))
                    insertData.append((data["BuildingId"], data["BuildingName"], data["RoomNumber"], data["RoomInfoUrl"], data["RoomUse"], data["RoomTotalArea"], data["RoomInsideArea"], data["RoomSaleStatus"], data["RoomShareArea"], data["Updatetime"]))
                else:
                    if fetchRowCnt[0][0] == data["RoomSaleStatus"]:
                        logger.warning("当前房屋信息存在数据库, 但销售状态未发生变更, BuildingId:{}, BuildingName:{}, RoomInfoUrl:{}, 无需UPDATE".format(data["BuildingId"], data["BuildingName"], data["RoomInfoUrl"]))
                    else:
                        logger.info("当前房屋信息存在数据库, 且销售状态发生变更, 原:{}, 现:{}, BuildingId:{}, BuildingName:{}, RoomInfoUrl:{}, 需执行UPDATE......".format(fetchRowCnt[0][0], data["RoomSaleStatus"], data["BuildingId"], data["BuildingName"], data["RoomInfoUrl"]))
                        dbExecute('UPDATE RoomDetailData SET RoomSaleStatus="{}", UpdateTime="{}" WHERE BuildingId="{}" AND RoomInfoUrl="{}"'.format(data["RoomSaleStatus"], data["Updatetime"], data["BuildingId"], data["RoomInfoUrl"]))
            if len(insertData) > 0:
                dbExecuteMany('INSERT INTO RoomDetailData(BuildingId, BuildingName, RoomNumber, RoomInfoUrl, RoomUse, RoomTotalArea, RoomInsideArea, RoomSaleStatus, RoomShareArea, UpdateTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', insertData)
        except Exception as e:
            logger.exception(str(e))

    def getRoomDetailInfo(self, data, **kwargs):
        global response
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
            data["RoomTotalPrice"] = int(parseHtml.xpath('//*[@id="ROOM_WJBAZJ"]/@value')[0]) if len(parseHtml.xpath('//*[@id="ROOM_WJBAZJ"]/@value')) > 0 else 0
            data["RoomUnitPrice"] = int(parseHtml.xpath('//*[@id="ROOM_WJBADJ"]/@value')[0]) if len(parseHtml.xpath('//*[@id="ROOM_WJBADJ"]/@value')) > 0 else 0
            data["RoomLocation"] = parseHtml.xpath('//*[@id="ROOM_FWZL"]/text()')[0]
            data["RoomInfoUrl"] = url
        except Exception as e:
            logger.exception(str(e))
            logger.warning("未能成功采集的数据:{}".format(json.dumps(data, ensure_ascii=False)))
