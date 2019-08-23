# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-23 15:16
# @Author  : lidong@immusician.com
# @Site    :
# @File    : exceptions.py

from sanic.handlers import ErrorHandler
from sanic.response import json
from failsafe import FallbacksExhausted


class CustomBaseException(Exception):
    """
    自定义错误基类
    """
    status_code = None
    code = 100001
    message = None
    error = None

    def __init__(self, error=None, code=None, message=None, status_code=None):
        super().__init__(message)
        if message:
            self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.error = error


class CustomExceptionHandler(ErrorHandler):
    """
    error handler
    """
    def default(self, request, exception):
        if isinstance(exception, CustomBaseException):
            data = {
                'msg': exception.message,
                'error': exception.code,
            }
            if exception.error:
                data.update({'error': exception.error})
            span = request['span']
            span.set_tag('http.status_code', str(exception.status_code))
            span.set_tag('error.kind', exception.__class__.__name__)
            span.set_tag('error.msg', exception.message)
            return json(data, status=exception.status_code)
        elif isinstance(exception, FallbacksExhausted):
            data = {
                'msg': "Request MS error: %s" % request.url,
                'data': repr(request.form),
                'error': 500,
            }
            return json(data, status=500)
        return super().default(request, exception)


class FailedRequest(CustomBaseException):
    status_code = 200
    message = "Failed Request"


class BadRequest(CustomBaseException):
    status_code = 400
    message = "Bad Request"


class Forbidden(CustomBaseException):
    status_code = 403
    message = "Not Found"


class NotFound(CustomBaseException):
    status_code = 404
    message = "Not Found"
