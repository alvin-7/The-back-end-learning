# -*-coding: utf-8 -*-
# @Time     :2020/3/31 18:32
# @Author   :zhuye
# @Func     :

"""
分布式锁：
1. try...finally 结构，finally中释放锁，保证无论try中逻辑是否正确，锁都能够被释放
2. 使用redis.set(key, value, ex=xx, nx=True)来生成一把有超时时间的锁
3. 为了保证每个开启锁和释放锁都正确，锁的值应该为客户端唯一标识值，且需要根据该值释放锁（如果锁的值不是该值，不应该释放）
4. 当成功生成锁之后，开启另外一个守护线程，该线程每隔1/3锁时间来检测锁是否还存在，如果存在，则延长锁时间，保证我们的逻辑在任何
情况下，都能够被执行完，并能够正确释放锁
"""

from threading import Thread

import redis
import time

#cli = redis.Redis(host='localhost', port=6379)		# 这个get出来的数据是byte
cli = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def Timer_ContiLock(cliID, iTime):
	#定时器：1/3time秒检测
	oldTime = int(time.time())
	while(cli.get("lock:1") == cliID):
		newTime = int(time.time())
		if (newTime - oldTime) >= int(iTime/3):
			oldTime = newTime
			cli.expire("lock:1", iTime)

# 开启锁的守护线程
def Lock_Guard(cliID, time):
	t = Thread(target=Timer_ContiLock, args=(cliID, time))
	t.start()

# 分布式锁, 使用同时开启另一线程，如果函数没执行完，锁生命周期1/3时间检查，并延长锁时间
def Do(cliID=str):
	try:
		# 当键不存在时设置键为lock:1的值为1，生存周期为10秒，返回True；当键存在时返回None
		iLockTime = 10
		iRet = cli.set("lock:1", cliID, ex=iLockTime, nx=True)
		if not iRet:
			return "The Key is Exist!"
		Lock_Guard(cliID, iLockTime)
		#do_something
		print(iRet)

	finally:
		if(str(cliID) == cli.get("lock:1")):
			pass
			#cli.delete("lock_1")

Do("1")