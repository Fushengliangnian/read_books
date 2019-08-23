# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-20 15:34
# @Author  : lidong@immusician.com
# @Site    :
# @File    : mongodb_conn.py
from motor import motor_asyncio


class MongoConnectionPool(object):
    MONGO_HOST = None
    MONGO_USER = None
    MONGO_PASSWORD = None
    MONGO_PORT = None
    MONGO_DATABASE = None
    pool = None

    def __init__(self, loop=None):
        self.conn = None
        self._loop = loop
        self._pool = None

    async def init(self, config, conn=None):
        if conn:
            self.conn = conn
        self.MONGO_HOST = config["host"]
        self.MONGO_PORT = config["port"]
        self.MONGO_DATABASE = config["database"]
        self.MONGO_PASSWORD = config["password"]
        self.MONGO_USER = config["user"]
        self._pool = motor_asyncio.AsyncIOMotorClient('mongodb://{}:{}@{}:{}'.format(
            self.MONGO_USER,
            self.MONGO_PASSWORD,
            self.MONGO_HOST,
            config["port"]))[self.MONGO_DATABASE]
        return self._pool

