# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     main.py
   Description :     主入口
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/3 22:23
-------------------------------------------------
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, wait

from apscheduler.executors.pool import ThreadPoolExecutor as ApsThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

import app.common.globalVars as globalVars
from app.common.settingReader import ConfigReader
from app.common.sqlite3 import initSqliteConnect, dbSelect, rebuildTable
from app.common.utils import loggers
from app.resources.spider import Spider
from app.resources.monitor import Monitor

executors = {
    "default": ApsThreadPoolExecutor(max_workers=3)
}
scheduler = BlockingScheduler(executors=executors, timezone='Asia/Shanghai')
conf = ConfigReader()
alarm = Monitor()


def findProjectDetailData():
    """
    全量采集地产项目信息
    :return:
    """
    rebuildTable()
    pageNum = spider.getPageNum()
    for i in range(1, pageNum):
        VIEWSTATE = globalVars.getValue("VIEWSTATE")
        VIEWSTATEGENERATOR = globalVars.getValue("VIEWSTATEGENERATOR")
        EVENTVALIDATION = globalVars.getValue("EVENTVALIDATION")
        asyncio.run(spider.pageListHtmlFindValue(i, VIEWSTATE, VIEWSTATEGENERATOR, EVENTVALIDATION))


def findRoomDetailData():
    """
    全量采集每个地产项目楼房信息
    :return:
    """
    sql = """SELECT PresaleDetailsInfoUrl FROM ProjectDetailData WHERE PermitNumber !='空' AND TimeToMarket BETWEEN DATE('now','start of month','-3 years') AND DATE('now')"""
    resultData = dbSelect(sql)
    pool = ThreadPoolExecutor(max_workers=int(conf.conf["DEFAULT"]["ThreadNum"]))
    futures = []
    for data in resultData:
        futures.append(pool.submit(spider.getPresaleInfo, {"PresellDetailsInfoUrl": data[0]}))
    wait(futures)


def monitor():
    """
    监控指定楼盘信息
    :return:
    """
    BuildingIds = conf.conf["Telegram"]["BuildingIds"].split(",")
    if len(BuildingIds) == 0:
        print("未添加房屋监控......")
        return
    pool = ThreadPoolExecutor(max_workers=int(conf.conf["DEFAULT"]["ThreadNum"]))
    futures = []
    for data in BuildingIds:
        futures.append(pool.submit(alarm.monitorIfNewHouseSaled, data))
    wait(futures)


if __name__ == '__main__':
    globalVars.init()
    globalVars.setValue("sqliteCon", initSqliteConnect())
    globalVars.setValue("VIEWSTATE", "")
    globalVars.setValue("VIEWSTATEGENERATOR", "")
    globalVars.setValue("EVENTVALIDATION", "")
    logger = loggers()
    spider = Spider()

    scheduler.add_job(func=findProjectDetailData, trigger="cron", hour=0, minute=1)
    scheduler.add_job(func=findRoomDetailData, trigger="cron", hour=5, minute=1)
    scheduler.add_job(func=monitor, trigger="interval", minutes=30)
    scheduler.start()
