# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     sqlite3.py
   Description :     
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/5 15:20
-------------------------------------------------
"""
import threading
import app.common.globalVars as globalVars
import sqlite3
from loguru import logger
from app.common.threadLock import acquire

mutex = threading.Lock()


def initSqliteConnect():
    return sqlite3.connect('config/RealEstateDataCollection.db', check_same_thread=False)


def dbSelect(sql):
    sqliteCon = globalVars.getValue("sqliteCon")
    sqliteCur = sqliteCon.cursor()
    try:
        sqliteCur.execute(sql)
        return sqliteCur.fetchall()
    except Exception as e:
        logger.exception(str(e))
        return []
    finally:
        sqliteCur.close()


def dbExecute(sql):
    logger.info(sql)
    sqliteCon = globalVars.getValue("sqliteCon")
    sqliteCur = sqliteCon.cursor()
    try:
        with acquire(mutex):
            sqliteCur.execute(sql)
            sqliteCon.commit()
    except Exception as e:
        sqliteCon.rollback()
        logger.exception(str(e))
    finally:
        sqliteCur.close()


def dbExecuteMany(sql, data: list):
    sqliteCon = globalVars.getValue("sqliteCon")
    sqliteCur = sqliteCon.cursor()
    try:
        with acquire(mutex):
            sqliteCur.executemany(sql, data)
            sqliteCon.commit()
    except Exception as e:
        sqliteCon.rollback()
        logger.exception(str(e))
    finally:
        sqliteCur.close()


def rebuildTable():
    sqliteCon = globalVars.getValue("sqliteCon")
    sqliteCur = sqliteCon.cursor()
    try:
        with acquire(mutex):
            sqliteCur.execute("DELETE FROM ProjectOverviewPageKey;")
            sqliteCon.commit()
            sqliteCur.execute("DELETE FROM sqlite_sequence WHERE name = 'ProjectOverviewPageKey';")
            sqliteCon.commit()
            sql = """CREATE TABLE IF NOT EXISTS `ProjectOverviewPageKey`(
                   Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                   ViewState VARCHAR NOT NULL,
                   ViewStateGenerator VARCHAR NOT NULL,
                   EventValidation VARCHAR NOT NULL,
                   CreateTime TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime'))
            );"""
            sqliteCur.execute(sql)
            sqliteCon.commit()
    except Exception as e:
        sqliteCon.rollback()
        logger.exception(str(e))
    finally:
        sqliteCur.close()