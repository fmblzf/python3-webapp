#coding:utf-8

"""测试类"""

import sys
#将db文件夹下的orm模块的路径添加到系统查找路径的集合中
sys.path.append('D:\\Program Files\\work\\workspace\\python35\\python3-webapp\\app\\db')
sys.path.append('D:\\Program Files\\work\\workspace\\python35\\python3-webapp\\app\\model')
import orm
from models import User,Blog,Comment
import asyncio

def test():
	loop = asyncio.get_event_loop()
	yield from orm.create_pool(loop,user='py',password='123456',db='awesome')
	print('kaishi')
	u = User(name='Test',email='test@example.com',passwd='1234567890',image='about:blank')

	yield from u.save()
	print('baocun')

f = test()
print(next(f))
	


