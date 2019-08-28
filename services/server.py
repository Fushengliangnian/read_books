# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-28 11:00
# @Author  : lidong@immusician.com
# @Site    :
# @File    : server.py
import logging

from sanic.blueprints import Blueprint

from common.server import app

_logger = logging.getLogger('sanic')
ab = Blueprint(__name__)
app.blueprints(ab)