# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-26 09:46
# @Author  : lidong@immusician.com
# @Site    :
# @File    : __init__.py

import os

from sanic.config import Config


def load_setting():
    conf = Config()
    module = os.environ.get('SANIC_SETTINGS_MODULE', 'settings')
    path = '%s.py' % module.replace('.', '/')
    conf.from_pyfile(path)
    return conf
