# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-20 15:33
# @Author  : lidong@immusician.com
# @Site    :
# @File    : utils.py
from common.server import app
from common.views import BaseAsyncHandler


def add_router(
        uri,
        handler,
        methods=frozenset({"GET"}),
        host=None,
        strict_slashes=None,
        version=None,
        name=None,
        stream=False,):
    print(1115)
    print(handler)
    if isinstance(handler, BaseAsyncHandler):
        print(77)
    app.add_route(handler, uri, methods, host, strict_slashes, version, name, stream)
