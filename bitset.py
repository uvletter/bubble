# -*- coding: utf-8 -*-
import struct
import os

from log import logger

class Bitset():
	"""A set designed with bit vector to save memory.
	Be careful the element of Bitset can only be integer"""
	
	__slots__=('__set')
	def __init__(self):
		self.__set = []

	def add(self, id):
		id = int(id)
		index = id // 8
		offset = id % 8

		# allocate space if necessary 
		delta = index + 1 - len(self.__set)
		if delta > 0:
			self.__set.extend([b'\0']*(delta))

		self.__set[index] = bytes([self.__set[index][0] | b'\x01'[0]<<offset])

	def remove(self, id):
		id = int(id)
		index = id // 8
		offset = id % 8

		self.__set[index] = bytes([self.__set[index][0] & (~(b'\x01'[0]<<offset))&255])

	def clear(self):
		self.__set = []

	def isnull(self):
		for i in range(len(self.__set)):
			if self.__set[i][0] != 0:
				return False
		return True

	def exist(self, id):
		id = int(id)
		index = id // 8
		offset = id % 8

		if index + 1 > len(self.__set):
			return False
		return self.__set[index][0] & b'\x01'[0]<<offset > 0

	def dump(self, filename='dump.bin'):
		'''
		For data persistence
		'''
		cwd = os.path.abspath(os.path.dirname(__file__))
		filepath = os.path.join(cwd, filename)
		with open(filepath, 'wb') as f:
			logger.info('Begin dumping set data')
			for b in self.__set:
				f.write(b)
			logger.info('Finish dumping')


	def recorve(self, filename='dump.bin'):
		'''
		Recover bitset from the dump file
		'''
		self.clear()
		cwd = os.path.abspath(os.path.dirname(__file__))
		filepath = os.path.join(cwd, filename)
		if os.path.exists(filepath) and os.path.isfile(filepath):
			logger.info('Begin recovering Bitset')
			with open(filepath, 'rb') as f:
				for b in f.read():
					self.__set.append(bytes([b]))
			logger.info('Finish recovering')

def test():
	bitset = Bitset()
	testcase1 = 10
	testcase2 = 28631
	testcase3 = 246
	testcase4 = 12
	testcase5 = 121

	bitset.add(testcase1)
	assert bitset.exist(testcase1)

	bitset.add(testcase2)
	assert bitset.exist(testcase1)
	assert bitset.exist(testcase2)


	bitset.add(testcase3)
	assert bitset.exist(testcase1)
	assert bitset.exist(testcase2)
	assert bitset.exist(testcase3)

	bitset.remove(testcase1)
	assert not bitset.exist(testcase1)
	assert bitset.exist(testcase2)
	assert bitset.exist(testcase3)

	bitset.remove(testcase2)
	for i in range(50000):
		if i!= testcase3:
			assert not bitset.exist(i)
		else:
			assert bitset.exist(i)

	bitset.add(testcase4)
	bitset.add(testcase5)
	bitset.dump('dump.bin')
	bitset.recorve('dump.bin')
	for i in range(50000):
		if i!= testcase3 and i!= testcase4 and i!= testcase5:
			assert not bitset.exist(i)
		else:
			assert bitset.exist(i)

	bitset.remove(testcase2)
	bitset.remove(testcase3)
	bitset.remove(testcase4)
	bitset.remove(testcase5)
	for i in range(50000):
		assert not bitset.exist(i)

	assert bitset.isnull()
	print('Pass the test')

if __name__ == '__main__':
	test()