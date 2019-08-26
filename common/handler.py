# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-23 16:30
# @Author  : lidong@immusician.com
# @Site    :
# @File    : views.py
from sanic.views import HTTPMethodView


class BaseAsyncHandler(HTTPMethodView):
    __instance = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance


if __name__ == '__main__':
    a = BaseAsyncHandler()
    b = BaseAsyncHandler()
    c = BaseAsyncHandler()
    d = BaseAsyncHandler()
    # e = B("1")
    # f = B("1")
    print(a)
    # print(b)
    # print(c)
    # print(d)
    # print(e)
    # print(f)
