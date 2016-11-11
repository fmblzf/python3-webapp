# -*- coding: utf-8 -*-

import asyncio,os,inspect,logging,functools

from urllib import parse

from aiohttp import web

from apis import APIError

#定义get装饰器
def get(path):
	'''
	Define decorator @get('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args,**kw):
			return func(*args,**kw)
		wrapper.__method__ = 'GET'
		wrapper.__route__ = path
		return wrapper
	return decorator

#定义post装饰器
def post(path):
	'''
	Define decorator @post('/path')
	'''
	def decorator(func):
		@functools(func)
		def wrapper(*args,**kw):
			return func(*args,**kw)
		wrapper.__method__ = 'POST'
		wrapper.__route__ = path
		return wrapper
	return decorator

#获取方法必须的关键参数
def get_required_kw_args(fn):
	args = []
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
			args.append(name)
	return tuple(args)

#获取被命名的关键字参数
def get_named_kw_args(fn):
	args = []
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			args.append(name)
	return tuple(args)

#是否有被命名的关键字参数
def has_named_kw_arg(fn):
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			return True

#是否有var_kw参数
def has_var_kw_arg(fn):
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.VAR_KEYWORD:
			return True

#是否有request参数
def has_request_arg(fn):
	sig = inspect.signature(fn)
	params = sig.parameters
	found = False
	for name,param in params.items():
		if name == 'request':
			found = True
			continue
		if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
			raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__,str(sig)))
	return found
	
'''创建request请求操作类'''	
class RequestHandler(object):
	"""docstring for RequestHandler"""
	def __init__(self, app,fn):
		self._app = app
		self._func = fn
		self._has_request_arg = has_request_arg(fn)
		self._has_var_kw_arg = has_var_kw_arg(fn)
		self._has_named_kw_args = has_named_kw_args(fn)
		self._named_kw_args = get_named_kw_args(fn)
		self._required_kw_args = get_required_kw_args(fn)

	#创建__call__方法
	@asyncio.coroutine
	def __call__(self,request):
		kw = None
		if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
			if request.method == 'POST':
				if not request.content_type:
					return web.HTTPBadRequest('Missing Content-Type.')
				ct = request.content_type.lower()
				if ct.startswith('application/json'):
					params = yield from request.json()
					if not isinstance(params,dict):
						return web.HTTPBadRequest('JSON body must be object.')
					kw = params
				elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
					params = yield from request.post()
					kw = dict(**params)
				else:
					return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)

			if request.method == 'GET':
				qs = request.query_string
				if qs:
					kw = dict()
					for k,v in parse.parse_qs(qs,True).items():
						kw[k] = v[0]
					



