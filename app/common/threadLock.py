# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     threadLock.py
   Description :     
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2022/8/5 16:59
-------------------------------------------------
"""
import threading
import app.common.globalVars as globalVars
from contextlib import contextmanager

from loguru import logger

# 用来存储local的数据
_local = threading.local()


@contextmanager
def acquire(*locks):
    # 对锁按照id进行排序
    locks = sorted(locks, key=lambda x: id(x))
    # 如果已经持有锁当中的序号有比当前更大的，说明策略失败
    acquired = getattr(_local,'acquired', [])
    if acquired and max(id(lock) for lock in acquired) >= id(locks[0]):
        logger.exception("Lock Order Violation")
        raise RuntimeError('Lock Order Violation')
    # 获取所有锁
    acquired.extend(locks)
    _local.acquired = acquired
    try:
        for lock in locks:
            lock.acquire()
        yield
    finally:
        # 倒叙释放
        for lock in reversed(locks):
            lock.release()
        del acquired[-len(locks):]
