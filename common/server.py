# -*- coding: utf-8 -*-
# !/usr/bin/env python
# @Time    : 2019-08-20 15:32
# @Author  : lidong@immusician.com
# @Site    :
# @File    : server.py

import asyncio
import gzip

# from basictracer import BasicTracer
from sanic import Sanic
from sanic.exceptions import RequestTimeout, NotFound, Forbidden, InvalidUsage
from sanic.response import json as Json, HTTPResponse
from schematics.exceptions import ValidationError, ConversionError, DataError

from common.exceptions import CustomExceptionHandler, BadRequest
from common.config import load_setting
from common.connections.mongodb_conn import MongoConnectionPool
from common.connections.redis_conn import RedisConnectionPool


DEFAULT_MIME_TYPES = frozenset([
    'text/html', 'text/css', 'text/xml',
    'application/json',
    'application/javascript'])


app = Sanic(__name__, error_handler=CustomExceptionHandler())
config = load_setting()
app.config = config


@app.listener('before_server_start')
async def before_server_start(app, loop):
    queue = asyncio.Queue()
    app.queue = queue
    # loop.create_task(consume(queue, app))
    # loop.create_task(service_watcher(app, loop))
    # loop.create_task(db_init(app, loop))
    # reporter = AioReporter(queue=queue)
    # tracer = BasicTracer(recorder=reporter)
    # tracer.register_required_propagators()
    # opentracing.tracer = tracer
    app.db = await MongoConnectionPool(loop=loop).init(config['DB_CONFIG'])
    app.redis = await RedisConnectionPool(loop=loop).init(app.config['REDIS_CONFIG'])

    # first load service
    # service = ServiceManager(loop=loop, host=app.config['CONSUL_AGENT_HOST'])
    # services = await service.discovery_services()
    # app.services = defaultdict(set)
    # for name in services[1].keys():
    #     s = await service.discovery_service(name)
    #     app.services[name].add(s[0])


# @app.listener('after_server_start')
# async def after_server_start(app, loop):
#     service = ServiceManager(app.name, loop=loop, host=app.config['CONSUL_AGENT_HOST'])
#     await service.register_service(port=app.config['PORT'])
#     app.service = service


@app.listener('before_server_stop')
async def before_server_stop(app, loop):
    await app.service.deregister()
    await app.queue.join()


@app.middleware('request')
async def cros(request):
    #     # request['start_time'] = time.time()
    #     config = request.app.config
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': config['ACCESS_CONTROL_ALLOW_ORIGIN'],
            'Access-Control-Allow-Headers': config['ACCESS_CONTROL_ALLOW_HEADERS'],
            'Access-Control-Allow-Methods': config['ACCESS_CONTROL_ALLOW_METHODS']
        }
        return Json({'error': 0}, headers=headers)
#
#     # span = before_request(request)
#     # request['span'] = span
#
    content_type = request.headers.get("content-type", "unknown")
    if request.method == 'POST' or request.method == 'PUT':
        if "application/json" in content_type:
            try:
                request['data'] = request.json
            except InvalidUsage as e:
                raise BadRequest(error=None, message=str(e))

        elif "application/x-www-form-urlencoded" or 'multipart/form-data' in content_type:
            request['data'] = {k: v[0] for k, v in request.form.items()}
        else:
            print('content_type_error:{}'.format(content_type))
    else:
        if request.args:
            request["data"] = {k: v[0] for k, v in request.args.items()}
#
#     _consume = route_specs[request.app.router.get(request)[0]].consumes
#     try:
#         request['data'] = valid_consume(_consume, request.get("data", {}))
#     except ValidationError as e:
#         raise BadRequest(error=None, message=str(e))
#     except ConversionError as e:
#         raise BadRequest(error=None, message=str(e))
#     except DataError as e:
#         raise BadRequest(error=None, message=str(e))


@app.middleware('response')
async def cors_res(request, response):
    span = request['span'] if 'span' in request else None
    if response is None:
        return response
    result = {'error': 0, "msg": "OK"}
    if not isinstance(response, HTTPResponse):
        if isinstance(response, tuple) and len(response) == 2:
            result.update({
                'data': response[0],
                'pagination': response[1]
            })
        else:
            if "msg" in response and "error" in response and "data" in response:
                result.update(response)
            else:
                result.update({'data': response})
        response = Json(result)
        if span:
            span.set_tag('http.status_code', "200")
    if span:
        span.set_tag('component', request.app.name)
        span.finish()
    response.headers["Access-Control-Allow-Origin"] = config['ACCESS_CONTROL_ALLOW_ORIGIN']
    response.headers["Access-Control-Allow-Headers"] = config['ACCESS_CONTROL_ALLOW_HEADERS']
    response.headers["Access-Control-Allow-Methods"] = config['ACCESS_CONTROL_ALLOW_METHODS']

    # gzip
    accept_encoding = request.headers.get('Accept-Encoding', '')
    content_length = len(response.body)
    content_type = response.content_type

    if ';' in response.content_type:
        content_type = content_type.split(';')[0]

    if (content_type not in DEFAULT_MIME_TYPES or
            'gzip' not in accept_encoding.lower() or
            not 200 <= response.status < 300 or
            (content_length is not None and
             content_length < 500) or
            'Content-Encoding' in response.headers):
        return response

    response.body = gzip.compress(response.body, compresslevel=6)

    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.body)

    vary = response.headers.get('Vary')
    if vary:
        if 'accept-encoding' not in vary.lower():
            response.headers['Vary'] = '{}, Accept-Encoding'.format(vary)
    else:
        response.headers['Vary'] = 'Accept-Encoding'

    # spend_time = round((time.time() - request['start_time']) * 1000)
    # print(spend_time)

    return response


@app.exception(RequestTimeout)
def timeout(request, exception):
    return Json({'message': 'Request Timeout'}, 408)


@app.exception(NotFound)
def notfound(request, exception):
    return Json(
        {'message': 'Requested URL {} not found'.format(request.url)}, 404)
