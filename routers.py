# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-23 16:24
# @Author  : lidong@immusician.com
# @Site    :
# @File    : routers.py
from common.server import app
from common.views import BaseAsyncHandler
from common.utils import add_router


@app.route("/demo")
def demo(request):
    print("ee")
    return {}


routers = [
    # restful class api
    add_router("/", BaseAsyncHandler.as_view()),
]

routers += [
    # all method function api
    add_router("/home", BaseAsyncHandler.home),
]
