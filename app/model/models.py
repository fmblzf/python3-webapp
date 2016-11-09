#coding:utf-8
import time,uuid,sys
sys.path.append('D:\\Program Files\\work\\workspace\\python35\\python3-webapp\\app\\db')
from orm import Model,StringField,BooleanField,FloatField,TextField

def next_id():
	return '%015d%s000' % (int(time.time()*1000),uuid.uuid4().hex)

if __name__ == '__main__':
	print(next_id())
 
