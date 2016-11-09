#coding:utf-8
import asyncio
import logging
import aiomysql

#log方法，打印信息
def log(sql,args=()):
	logging.info('SQL: %s' % sql)

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
		logging.info('rows returned: %s' % len(rs))
		return rs

#封装insert,update,delete方法
@asyncio.coroutine
def execute(sql,args):
	log(sql)
	with(yield from __pool) as conn:
		if not autocommit:
			yield from conn.begin()
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?','s%'),args)
			affected = cur.rowcount
			yield from cur.close()
			if not autocommit:
				yield from conn.commit()
		except BaseException as e:
			if not autocommit:
				yield from conn.rollback()
			raise
		return affected




"""
	ORM代码编写
"""
#为insert的values创建sql中的占位符
def create_args_string(num):
	L = []
	for i in range(num):
		L.append('?')
	return ','.join(L)

#字段基类
class Field(object):

	def __init__(self,name,column_type,primary_key,default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		return '<%s,%s:%s>' % (self.__class__.__name__,self.column_type,self.name)

#字符串类型
class StringField(Field):

	def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
		super(StringField,self).__init__(name, ddl,primary_key,default)

#布尔类型
class BooleanField(Field):
	"""docstring for BooleanField"""
	def __init__(self, name=None,default=False):
		super(BooleanField, self).__init__(name,'boolean',False,default)

#整形类型
class IntegerField(Field):
	"""docstring for IntegerField"""
	def __init__(self, name=None,primary_key=False,default=0):		
		super(IntegerField, self).__init__(name,'bigint',primary_key,default)

#浮点类型
class FloatField(Field):
	"""docstring for FloatField"""
	def __init__(self, name=None,primary_key=False,default=0.0):
		super(FloatField, self).__init__(name,'real',primary_key,default)

#文本类型
class TextField(Field):
	"""docstring for TextField"""
	def __init__(self, name=None,default=None):
		super(TextField, self).__init__(name,'text',False,default)		

#ModelMetaclass 读取子类的映射信息
class ModelMetaclass(type):
	"""docstring for ModelMetaclass"""
	def __new__(cls,name,bases,attrs):
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
		attrs['__insert__'] = 'insert into `%s`(%s,`%s`) values(%s)' % (tableName,','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName,','.join(map(lambda f:'`%s=?`' % (mappings.get(f).name or f),fields)),primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName,primaryKey)
		return type.__new__(cls,name,bases,attrs)
		
#所有对应的基类
class Model(dict,metaclass=ModelMetaclass):
	"""docstring for Model"""
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)
		
	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s' " % key)

	def __setattr__(self,key,value):
		self[key] = value

	def getValue(self,key):
		return getattr(self,key,None)

	def getValueOrDefault(self,key):
		value = getattr(self,key,None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s:%s' % (key,str(value)))
				setattr(self,key,value)
		return value

	#创建类方法，所有的子类都可以访问
	@classmethod
	@asyncio.coroutine
	def find(cls,pk):
		logging.info(' find object by primary key.')
		rs = yield from select('%s where `%s`=?' % (cls.__select__,cls.__primary_key__),[pk],1)
		if len(rs) == 0:
			return None
		return cls(**rs[0])

	#类方法，查找所有的结果集
	@classmethod
	@asyncio.coroutine
	def findAll(cls,where=None,args=None,**kw):
		' find objects by where clause. '
		sql = [cls__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get('orderBy',None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit',None)
		if limit is not None:
			sql.append('limit')
			if isinstance(limit,int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit,tuple) and len(limit) == 2:
				sql.append('?,?')
				args.extend(limit)
			else:
				raise ValueError('Invalid limit value：%s' % str(limit))
		rs = yield from select(' '.join(sql),args)
		return [cls(**r) for r in rs]
	
	#创建类方法，查询指定表的数据数量			
	@classmethod
	@asyncio.coroutine
	def findNumber(cls,selectField,where=None,args=None):
		' find number by select and where. '
		sql = ['select %s _num_ from `%s`' % (selectField,cls.__table__)]
		if where:
			sql.append('where')
			sql.append(where)
		rs = yield from select(' '.join(sql),args,1)
		if len(rs) == 0:
			return None
		return ra[0]['_num_']


	#创建实例方法，所有的子类的实例都可以调用
	@asyncio.coroutine
	def save(self):
		args = list(map(self.getValueOrDefault,self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__insert__,args)
		if rows != 1:
			logging.warn('failed to insert record: affected rows: %s' % rows)


	#创建实例方法，实现数据更新
	@asyncio.coroutine
	def update(self):
		args = list(map(self.getValueOrDefault,self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__update__,args)
		if rows != 1:
			logging.warn(' failed to update by primary key : affected rows：%s' % rows)

	#创建实例方法，实现移除该实例
	@asyncio.coroutine
	def remove(self):
		args = [self.getValue(self.__primary_key__)]
		rows = yield from execute(self.__delete__,args)
		if rows != 1:
			logging.warn(' failed to remove by primary key：affected rows: %s' % rows)




		
