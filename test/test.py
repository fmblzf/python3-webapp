#coding:utf-8

"""测试类"""

import sys
#将db文件夹下的orm模块的路径添加到系统查找路径的集合中
sys.path.append('D:\\Program Files\\work\\workspace\\python35\\python3-webapp\\app\\db')
sys.path.append('D:\\Program Files\\work\\workspace\\python35\\python3-webapp\\app\\model')
import orm
from models import User,Blog,Comment

def test():
	yield from orm.create_pool(None,user='py',password='123456',db='awesome')

	u = User(name='Test',email='test@example.com',passwd='1234567890',image='about:blank')

	yield from u.save()

for x in test():
	pass


