#coding:utf-8
import asyncio
import logging
import aiomysql

#log方法，打印信息
def log(sql,args=()):
	logging.info(sql)

#创建数据库连接池
@asyncio.coroutine
def create_pool(loop,**kw):
	logging.info('create database connection pool...')
	#定义全部变量，数据库连接池
	global __pool
	__pool = yield from aiomysql.create_pool(
		host=kw.get('host','localhost'),
		port=kw.get('port',3306),
		user=kw['user'],
		password=kw['password'],
		db=kw['db'],
		charset=kw.get('charset','utf-8'),
		autocommit=kw.get('autocommit',True),
		maxsize=kw.get('maxsize',10),
		minsize=kw.get('minsize',1),
		loop=loop
	)

#封装select方法
@asyncio.coroutine
def select(sql,args,size=None):
	log(sql,args)
	global __pool
	with(yield from __pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?','%s'),args or ())
		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall()
		yield from cur.close()
		logging.info('rows returned:%s' % len(rs))
		return rs

#封装insert,update,delete方法
@asyncio.coroutine
def execute(sql,args):
	log(sql)
	with(yield from __pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?','s%'),args)
			affected = cur.rowcount
			yield from cur.close()
		except BaseException as e:
			raise
		return affected

#为insert的values创建sql中的占位符
def create_args_string(num):
	L = []
	for i in range(num):
		L.append('?')
	return ','.join(L)

#ModelMetaclass 读取子类的映射信息
class ModelMetaclass(type):
	"""docstring for ModelMetaclass"""
	def __init__(cls,name,bases,attrs):
		#排除model基类本身
		if name == 'Model':
			return type.__new__(cls,name,bases,attrs)
		#获取table名称,如果表名和类名一样，就不设置__table__属性，直接调用类名
		tableName = attrs.get('__table__',None) or name
		logging.info('found model：%s (table:%s)' % (name,tableName))
		#获取所有的Fields和主键名：
		mappings = dict()
		fields = []
		primaryKey = None
		for k,v in attrs.items():
			if isinstance(v,Field):
				logging.info(' found mappings: %s==>%s' % (k,v))
				mappings[k] = v
				if v.primary_key:
					#找到主键
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field:%s' % k)
					primaryKey = k
				else:
					fields.append(k)
		if not primaryKey:
			raise RuntimeError('Primary key not found')
		for k in mappings:
			attrs.pop(k)
		escaped_fields=list(map(lambda f:'`%s`' % f,fields))
		#保存属性和列的映射关系
		attrs['__mappings__'] = mappings
		#表名
		attrs['__table__'] = tableName
		#主键属性名称
		attrs['__primary_key__'] = primaryKey
		#除了主键外的属性名称：
		attrs['__fields__'] = fields
		#构造默认的SELECT,INSERT,UPDATE和DELETE语句：
		attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey,','.join(escaped_fields),tableName)
		attrs['__insert__'] = 'insert into `%s`(%s,`%s`) values(%s)' % (tableName,','.json(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName,','.join(map(lambda f:'`%s=?`' % f,)))
		attrs['__delete__'] = ''
		super(ModelMetaclass, self).__init__()
		self.arg = arg
		
