#!/usr/bin/env python
# -*-coding: utf-8 -*-
# @Time     :2019/12/5 11:00
# @Author   :zhuye
# @Func     :用于A*寻路算法演算过程

"""
A*算法
NOTE:F = G + H   G:从起始点到当前点值， H:从当前点到目标点值
步骤：
1.将起始点加入到开启列表
2.重复以下工作：
	a.寻找开启列表中F值最小的点，设置为当前点
	b.将其切换到关闭列表中
	c.对当前点临近点A们进行F值计算
		*.如果A不可通过或者已经在关闭列表中，略过
		*.如果A不在开启列表中，则添加进去，并将A的父节点指向当前点，并计算F,G,H值
		*.如果A已经在开启列表中，用G值作为参考检测新的路径是否更好，更低的G值意味着更好的路线。如果G值要小于之前G值，
		则让A点的父节点改成当前点，并重新计算A的F,G,H值。如果开启列表有排序，此时需要重新排序
		（这里的G值计算应该是当前点的G值加上当前点到A点的G值，并与之前的G值比较）
	d.停止，当
		*.把目标格加入到关闭列表中，此时路线已被找到
		*.没有找到目标格，开启列表已经空了。这时候路径不存在
3.保存路径，从目标格开始，往上遍历父节点，即是我们需要的路径
"""

class CNode(object):
	m_Slant = 14  # 倾斜值
	m_UDLR = 10  # 上下左右值

	def __init__(self, x, y, isWall, oParent):
		self.m_Parent = oParent  # 父节点
		self.m_tVal = (x, y)  # 当前节点位置信息
		self.m_IsWall = isWall  # 是否为墙
		self.m_F = 0  # F值
		self.m_G = 0  # G值，开始节点到此节点值
		self.m_H = 0  # H值，目标节点到此节点值

	def DoCalFGH(self, oParentNode, oEndNode):
		"""
		此函数只用来计算oParentNode邻近点的值
		且会使得该节点的父节点指向parentNode
		:param oParentNode: 父节点
		:param oEndNode: 目的节点
		:return:
		"""
		x, y = self.m_tVal
		self.m_H = (abs(oEndNode.m_tVal[0] - x) + abs(oEndNode.m_tVal[1] - y)) * self.m_UDLR
		if abs(oParentNode.m_tVal[0] - x) != 0 and abs(oParentNode.m_tVal[1] - y) != 0:
			self.m_G = oParentNode.m_G + self.m_Slant
		else:
			self.m_G += oParentNode.m_G + self.m_UDLR
		self.m_F = self.m_G + self.m_H
		self.m_Parent = oParentNode

MAX_TIMES = 9999  # 循环最大次数

class CAStart:
	m_tDir = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1),)

	def __init__(self, mazeLis, tStart, tEnd):
		self.m_OpenList = []  # 开启列表		[(),()]
		self.m_CloseList = []  # 关闭列表	[(),()]
		self.m_MazeNode = None
		self._InitMaze(mazeLis)
		self.m_CurPoint = self._GetNode(tStart)  # 当前点		CNode
		self.m_DonePoint = self._GetNode(tEnd)  # 目的节点	CNode
		self.m_isDone = False  # 是否寻路完	bool
		self.FindPath()

	# 计算路径
	def FindPath(self):
		if not self.m_CurPoint or not self.m_DonePoint:
			return
		self.m_OpenList.append(self.m_CurPoint)
		for _ in range(MAX_TIMES):
			if not self.m_OpenList:
				return
			self.m_CurPoint = None
			# a
			# 寻找打开列表中F值最小的节点，并设置为当前节点
			for oPoint in self.m_OpenList:
				if not self.m_CurPoint or self.m_CurPoint.m_F > oPoint.m_F:
					self.m_CurPoint = oPoint
			# b
			self.m_OpenList.remove(self.m_CurPoint)
			self.m_CloseList.append(self.m_CurPoint)
			# c
			iX, iY = self.m_CurPoint.m_tVal
			for tDir in self.m_tDir:
				oNode = self._GetNode((iX + tDir[0], iY + tDir[1]))
				if not oNode:
					continue
				if oNode.m_IsWall:
					continue
				if oNode in self.m_CloseList:
					continue
				if oNode in self.m_OpenList:
					oNewNode = self._ReInitNode(oNode, self.m_CurPoint)
					if oNode.m_G == 0 or oNewNode.m_G < oNode.m_G:
						self.m_OpenList.remove(oNode)
						self.m_OpenList.append(oNewNode)
				else:
					oNode.DoCalFGH(self.m_CurPoint, self.m_DonePoint)
					self.m_OpenList.append(oNode)
					if oNode.m_tVal == self.m_DonePoint.m_tVal:
						self.m_isDone = True
						self.m_DonePoint = oNode
						return

	# 获得计算后的路径
	def GetPath(self):
		pathLis = []
		if not self.m_isDone or not self.m_DonePoint:
			return pathLis
		pathPoint = self.m_DonePoint
		for _ in range(MAX_TIMES):
			pathLis.append(pathPoint.m_tVal)
			if not pathPoint.m_Parent:
				pathLis.reverse()
				print("IsDone:", self.m_isDone)
				print("TheEnd:", self.m_DonePoint.m_tVal)
				return pathLis
			pathPoint = pathPoint.m_Parent

	def _InitMaze(self, mazeLis):
		self.m_iRow = len(mazeLis)
		self.m_iCol = len(mazeLis[0])
		self.m_MazeNode = [None] * self.m_iRow
		for i in range(self.m_iRow):
			if self.m_MazeNode[i] is None:
				self.m_MazeNode[i] = [None] * self.m_iCol
			for j in range(self.m_iCol):
				if mazeLis[i][j] != 1:
					isWall = True
				else:
					isWall = False
				self.m_MazeNode[i][j] = CNode(i, j, isWall, None)

	def _ReInitNode(self, oldNode, oParent):
		oNewNode = CNode(oldNode.m_tVal[0], oldNode.m_tVal[1], oldNode.m_IsWall, oParent)
		oNewNode.DoCalFGH(oParent, self.m_DonePoint)
		return oNewNode

	def _GetNode(self, tPoint):
		if tPoint[0] < 0 or tPoint[1] < 0:
			return None
		if self.m_iRow - 1 < tPoint[0] or self.m_iCol - 1 < tPoint[1]:
			return None
		return self.m_MazeNode[tPoint[0]][tPoint[1]]
