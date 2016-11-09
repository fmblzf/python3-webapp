#coding:utf-8
import time,uuid,sys
#将db文件夹下的orm模块的路径添加到系统查找路径的集合中
sys.path.append('D:\\Program Files\\work\\workspace\\python35\\python3-webapp\\app\\db')
#导入orm模块
from orm import Model,StringField,BooleanField,FloatField,TextField
#创建生成主键的方法
def next_id():
	return '%015d%s000' % (int(time.time()*1000),uuid.uuid4().hex)

#用户对象
class User(Model):
	"""docstring for User"""

	__table__ = 'users'

	id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
	email = StringField(ddl='varchar(50)')
	passwd = StringField(ddl='varchar(50)')
	admin = BooleanField()
	name = StringField(ddl='varchar(50)')
	image = StringField(ddl='varchar(500)')
	created_at = FloatField(default=time.time)

#博客对象
class Blog(Model):
	"""docstring for Blog"""
	
	__table__ = 'blogs'

	id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
	user_id = StringField(ddl='varchar(50)')
	user_name = StringField(ddl='varchar(50)')
	user_image = StringField(ddl='varchar(500)')
	name = StringField(ddl='varchar(50)')
	summary = StringField(ddl='varchar(200)')
	content = TextField()
	created_at = FloatField(default=time.time)

#评论对象
class Comment(object):
	"""docstring for Comment"""
	__table__ = 'comments'

	id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
	blog_id = StringField(ddl='varchar(50)')
	user_id = StringField(ddl='varchar(50)')
	user_name = StringField(ddl='varchar(50)')
	user_image = StringField(ddl='varchar(500)')
	content = TextField()
	created_at = FloatField(default=time.time)



if __name__ == '__main__':
	print(next_id())
 
