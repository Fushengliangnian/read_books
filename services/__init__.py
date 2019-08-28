# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-26 10:16
# @Author  : lidong@immusician.com
# @Site    :
# @File    : __init__.py


class Service(object):
    @classmethod
    def instance(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        assert not hasattr(self.__class__, '_instance'), 'Do not call constructor directly!'
        self.ab_testing_event_service = EventService(self)
        self.ab_testing_project_service = ABTestingProjectService(self)
        self.ab_testing_indicator_service = ABTestingIndicatorService(self)


class BaseService(object):
    def __init__(self, services):
        self.mongo_conn = MongoConn.instance()
        # 异步Mongo-motor
        self.motor_conn = MotorConn.instance()
        self.redis_conn = RedisConn.instance().conn
        self.redis_conn2 = RedisConn2.instance().conn
        self.redis_conn3 = RedisConn3.instance().conn
        self.ssdb_conn = SSDBConn.instance().conn
        self.services = services
        self.empty_cursor = EmptyCursor()
