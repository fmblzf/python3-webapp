#coding:utf-8
import math
#生成器
def simple_generator_function():
	yield 1
	yield 2
	yield 3

for value in simple_generator_function():
	print(value)


generator_t = simple_generator_function()

print('next  '+str(next(generator_t)))
print('next  '+str(next(generator_t)))
print('next  '+str(next(generator_t)))

def test_generator_fun(num):
	if num % 2 == 0:
		yield num
	num += 1

for value in test_generator_fun(4):
	print(value)

t_test = test_generator_fun(4)
print(next(t_test))
#判断一个数是否是素数
def is_primes(number):
	if number>1:
		if number == 2:
			return True
		for current in range(2,int(math.sqrt(number))+1):
			if number % current == 0:
				return False
		return True
	return False
#获取比start大的所有素数，这里获取了比start大的所有素数的生成器（迭代器）
def get_promes(start):
	while True:
		if is_primes(start):
			yield start
		start += 1


#获取大于3小于2000的素数
def t_fun():
	total = 0
	for value in get_promes(3):
		if value < 2000:
			total += value
		else:
			return total

print(t_fun())
#pep34:实现先返回yield的值，再给number赋值传过来的值
def get_primes1(number):
	while True:
		if is_primes(number):
			number = yield number
		number += 1

def print_successive_primes(iter,base=10):
	prime_generator = get_primes1(base)
	#send(None),将生成器的位置定位到yield位置，并且执行一次返回，因为None所有不赋值
	print('send-none'+str(prime_generator.send(None)))
	for power in range(iter):
		#将send的参数值赋给yield的值，然后接下来往下执行
		print(prime_generator.send(power * base))

print_successive_primes(10)



