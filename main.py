# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-20 16:09
# @Author  : lidong@immusician.com
# @Site    :
# @File    : main.py
from common.server import app
from routers import routers


if __name__ == '__main__':
    # app.add_route(BaseAsyncHandler.as_view(), "/")
    app.run(debug=True)
