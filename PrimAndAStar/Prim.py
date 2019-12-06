#!/usr/bin/env python
# -*-coding: utf-8 -*-
# @Time     :2019/12/5 15:28
# @Author   :zhuye
# @Func     :Prim迷宫建造算法

import random
import time

def GetArray(x=0, y=0):
	if not x or not y:
		return []
	arrayLis = [None] * x
	for i in range(x):
		for j in range(y):
			if i % 2 == 1 and j % 2 == 1:
				z = 3
			else:
				z = 0
			if arrayLis[i] is None:
				arrayLis[i] = []
			arrayLis[i].append(z)
	return arrayLis

class CMaze(object):
	"""
	1.让迷宫全是墙（0）
	2.选一个单元格作为迷宫的通路（1），然后把他的邻墙（0#）放入列表
	2.当列表里还有墙（0）时：
		*.从列表中随机选一个墙（0），如果这面墙分隔的两个单元格只有一个单元格被访问过
			1.那就从列表中移除这面墙，即把墙打通，让未访问的单元格成为迷宫的通路
			2.把这个格子的墙加入列表
		*.如果墙两面的单元格都已经被访问过，那就从列表里移除这面墙
	"""
	m_tDir = ((0, 1), (0, -1), (1, 0), (-1, 0))

	def __init__(self, x, y, x1, y1):
		self.m_rows = x
		self.m_cols = y
		self.m_checkLis = []
		self.m_endLis = []
		self.m_mazeLis = GetArray(x, y)
		self.SetStart(x1, y1)

	def SetStart(self, x, y):
		self.m_tStart = (x, y)
		self.m_mazeLis[x][y] = 1
		self.m_history = [(x, y)]

	def GetEnd(self):
		if not hasattr(self, "m_tEnd"):
			for i in range(self.m_rows):
				for j in range(self.m_cols):
					if (i == 0 or i == self.m_rows - 1) or (j == 0 or j == self.m_cols - 1):
						if not (i, j) == self.m_tStart and i > self.m_rows // 2 and self.m_mazeLis[i][j] == 1\
								and abs(i-self.m_tStart[0]) > self.m_rows/2 and abs(j-self.m_tStart[1]) > self.m_cols/2:
							self.m_endLis.append((i, j))
			self.m_tEnd = random.choice(self.m_endLis)
		return self.m_tEnd

	def CreateMaze(self):
		while(self.m_history):
			r, c = random.choice(self.m_history)
			self.m_checkLis.append((r, c))
			count1 = 0
			count2 = 0
			for k, v in self.m_tDir[:2]:
				if (r + k) in range(self.m_rows) and (c + v) in range(self.m_cols):
					if (r + k, c + v) in self.m_checkLis:
						count1 += 1
			for k, v in self.m_tDir[2:]:
				if (r + k) in range(self.m_rows) and (c + v) in range(self.m_cols):
					if (r + k, c + v) in self.m_checkLis:
						count2 += 1
			if count1 <= 1 and count2 <= 1:
				self.m_mazeLis[r][c] = 1
				for k, v in self.m_tDir:
					if (r + k) in range(self.m_rows) and (c + v) in range(self.m_cols):
						if self.m_mazeLis[r + k][c + v] == 0:
							self.m_history.append((r + k, c + v))
			self.m_history.remove((r, c))

		foorSize = random.randint(self.m_rows, self.m_rows + self.m_cols)
		fSize = 0
		for i in range(self.m_rows):
			for j in range(self.m_cols):
				if self.m_mazeLis[i][j] == 1:
					continue
				if random.randint(0, 100) > 20:
					continue
				fSize += 1
				if fSize > foorSize:
					continue
				self.m_mazeLis[i][j] = 1

	def PrintMaze(self):
		mazeLis = self.m_mazeLis
		for row in range(self.m_rows):
			for col in range(self.m_cols):
				iResult = mazeLis[row][col]
				if iResult == 1:
					print("□", end="")
				elif iResult in (0, 3):
					print("■", end="")
			print()
		print()

