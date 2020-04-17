# -*- coding: utf-8 -*-

import collections
import time
import hashlib
import importlib
import functools

"""
定时器-by时间轮
使用字典简单实现的形式
"""


class CTimeWheel:
    def __init__(self):
        self._time_wheel = collections.defaultdict(list)
        self._key2task = {}     #{hash:CTimeTask}
        self._timer = self.now()

    def add_time(self, delay, skey, func_name, *args, **kwargs):
        """
        添加一个定时任务
        :param delay:延迟时间，单位 1/100 秒
        :param skey:定时器唯一标识
        :param func_name:回调函数名
        :param args:回调参数
        :param kwargs:回调字典参数
        :return:
        """
        hash_val = self.hash_skey(skey)
        if hash_val in self._key2task:
            raise Exception("clash %s:%s" % (skey, hash_val))
        iTaskTime = int(time.time()*100) + delay
        oTask = CTimeTask(hash_val, func_name, *args, **kwargs)
        self._time_wheel[iTaskTime].append(oTask)
        self._key2task[hash_val] = oTask

    def remove_key(self, skey):
        hash_val = self.hash_skey(skey)
        if hash_val not in self._key2task:
            return
        self._key2task[hash_val].close()

    def loop_time(self):
        inow = self.now()
        for itime in range(self._timer, inow + 1):
            if itime not in self._time_wheel:
                continue
            tasklist = self._time_wheel.pop(itime)
            if not tasklist:
                continue
            for otask in tasklist:
                otask.run_task()
                del self._key2task[otask.get_hash()]
        self._timer = inow + 1

    def hash_skey(self, skey):
        """
        对sKey进行hash
        :param skey:
        :return: 十六进制结果
        """
        return int(hashlib.md5(skey.encode('utf-8')).hexdigest(), 16)

    def now(self):
        """
        :return:当前 1/100 秒为单位的值
        """
        return int(time.time() * 100)

class CTimeTask(object):
    def __init__(self, hash_val, func_name, *args, **kwargs):
        self._hash_val = hash_val
        self._func_name = func_name
        self._args = args
        self._kwargs = kwargs
        self._isrun = True
        print(self._args, "\n", self._kwargs)


    def run_task(self):
        if self._isrun == False:
            return
        plits = self._func_name.split('.')
        if len(plits) < 2:
            raise Exception("funcname err %s" % (self._func_name))
        smodule = '.'.join(plits[:-1])
        sfunc = plits[-1]
        module = importlib.import_module(smodule)
        funcobj = getattr(module, sfunc, None)
        if funcobj:
            ofunc = functools.partial(funcobj, *self._args, **self._kwargs)
            ofunc()

    def get_hash(self):
        return self._hash_val

    def close(self):
        self._isrun = False


def test(a, b, c, d):
    print('test', time.time())
    print(f"{a}-{b}-{c} {d}")

if __name__ == "__main__":
    oTime = CTimeWheel()
    print('start', time.time())
    oTime.add_time(1 * 100, "test", "timewheel.test", 1, 2, 3, 4)
    oTime.add_time(10 * 100, "test2", "timewheel.test", 7, 8, 9, {1:'11111'})
    oTime.add_time(15 * 100, "test3", "timewheel.test", 10, 11, 12, {2: '11111'})
    while(1):
        oTime.loop_time()
    # func = functools.partial(test, 1,2,3)
    # func()

