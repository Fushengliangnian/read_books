# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-23 16:30
# @Author  : lidong@immusician.com
# @Site    :
# @File    : views.py
from sanic.views import HTTPMethodView, CompositionView

from common.server import app


class BaseAsyncHandler(HTTPMethodView):
    def dispatch_request(self, request, *args, **kwargs):
        print(self.__dict__)
        print("##########3")
        handler = getattr(self, request.method.lower(), None)
        return handler(request, *args, **kwargs)

    async def get(self, request):
        print(request.app.router.__dict__)
        return {}

    async def home(self, request):
        print("home")
        return {}


print(111)
# app.add_route(BaseAsyncHandler.as_view(), "")
