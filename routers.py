# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-23 16:24
# @Author  : lidong@immusician.com
# @Site    :
# @File    : routers.py
from common.server import app
from common.handler import BaseAsyncHandler

add_router = app.add_route

routers = [
    # restful class api
    add_router("/", BaseAsyncHandler.as_view()),
]

routers += [
    # all method class function api
    # add_router("/home", BaseAsyncHandler().home),
]
