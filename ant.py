# -*- coding: utf-8 -*-
import os
import multiprocessing
import json
import time

import requests

import mq
from bitset import Bitset
from log import logger

REDIS_HOST=None # Yous redis server ip. Need to set
REDIS_AUTH=None # Your redis server auth. Need to set
AUTO_RECOVER=True # Revocer the hashset from the dump file. Default is true


'''A micro crawl framework, which supports distributed system and multi-process
It requires redis as the message queue communicating among machines and processes.
'''

class Task(object):
	"""The base class of task.
	:param id: the unique identification of task
	:param retry: True if the task is enforced
	:param topic: the topic of the task, by which task is coupled with the crawl function."""
	def __init__(self, id, **kw):
		super(Task, self).__init__()
		self.id = id
		self.__dict__.update(kw)

		if 'retry' not in self.__dict__:
			self.retry = False

		if 'topic' not in self.__dict__:
			self.topic = '_default'

class Ant(object):
	task_class = Task
	hashset_class = Bitset

	def __init__(self,name):
		super(Ant, self).__init__()
		self.name = name
		self.assemble_mq = mq.Mq(name + '_assemble', host=REDIS_HOST, password=REDIS_AUTH)
		self.distribute_mq = mq.Mq(name + '_distribute', host=REDIS_HOST, password=REDIS_AUTH)

	def publish_task(self, task):
		self.assemble_mq.push(task)


class Worker(Ant):

	def __init__(self, name):
		super(Worker, self).__init__(name)
		self.crawl_funcs = {}
		self.parser_funcs = {}
		self.session = requests.Session()
	
	def _routine(self):
		try:
			while True:
				pop_data = self.distribute_mq.pop()
				if pop_data == None:
					logger.info('There is no work to do. Process {0} will sleep 5 seconds.'.format(os.getpid()))
					time.sleep(5)
					continue

				task = Worker.task_class(**pop_data)
				self._handle(task)
		except KeyboardInterrupt:
			pass
		except BaseException as error:
			logger.exception('PID {0} Error: {1}'.format(os.getpid(), error))

	def _handle(self, task):
		if task.topic not in self.crawl_funcs:
			raise Exception('Cannot find the crawl function of topic {0}, task id {1}'.format(task.topic, task.id))

		try:
			for crawl in self.crawl_funcs[task.topic]:
				response = crawl(task)
				if crawl.__name__ in self.parser_funcs:
					for parser in self.parser_funcs[crawl.__name__]:
						parser(response)
		except Exception as e:
			logger.exception('Process {0} raise an exception: '.format(os.getpid()))
			time.sleep(60)
			task.retry = True
			self.publish_task(task)

	def crawl(self, topic='_default'):
		'''Decorator for registering the crawl functions
		:param topic: the topic of the crawl function
		'''
		def decorator(f):
			if topic not in self.crawl_funcs:
				self.crawl_funcs[topic] = []

			self.crawl_funcs[topic].append(f)
			return f
		return decorator

	def parser(self, *args):
		'''Decorator for registering parser functions which parse the responses of crawl
		:param target: target crawl function
		'''
		def decorator(f):
			for target in args:
				if target.__name__ not in self.parser_funcs:
					self.parser_funcs[target.__name__] = []

				self.parser_funcs[target.__name__].append(f)
			return f
		return decorator

	def run(self, n, header={}, cookies={}):
		logger.info('Worker ants start working...')

		self.session.headers.update(header)
		self.session.cookies.update(cookies)

		pool = []
		for i in range(n):
			p = multiprocessing.Process(target = self._routine)
			p.start()
			pool.append(p)

		for p in pool:
			p.join()

		logger.info('Worker ants quit')


class Queen(Ant):

	def __init__(self,name):
		super(Queen, self).__init__(name)
		self.hset = self.hashset_class()

		if AUTO_RECOVER:
			self.hset.recorve()


	def _routine(self):
		while True:
			pop_data = self.assemble_mq.pop()
			if pop_data == None:
				logger.info('There is no work to do. Process {0} will sleep 5 seconds.'.format(os.getpid()))
				time.sleep(5)
				continue

			task = self.task_class(**pop_data)
			if not task.retry:
				if not self.hset.exist(task.id):
					self.distribute_mq.push(task)
					self.hset.add(task.id)
			else:
				self.distribute_mq.push(task)
	
	def run(self, first_task):
		logger.info('Queen ant start working...')

		self.distribute_mq.push(first_task)

		try:
			self._routine()
		except BaseException as error:
			logger.exception('Error: {1}'.format(os.getpid(), error))
		finally:
			self.hset.dump()

		logger.info('Program exit')

g = {}