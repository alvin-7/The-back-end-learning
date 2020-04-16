#!/usr/bin/env python
# -*-coding: utf-8 -*-
# @Time     :2019/12/5 15:28
# @Author   :zhuye
# @Func     :Main

from Prim import CMaze
from A_Star import CAStart

if __name__ == "__main__":
	oMaze = CMaze(10, 10, 0, 0)
	oMaze.CreateMaze()
	oMaze.PrintMaze()

	print(oMaze.GetEnd())
	oFind = CAStart(oMaze.m_mazeLis, (0, 0), oMaze.GetEnd())
	print(oFind.GetPath())