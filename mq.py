# -*- coding: utf-8 -*-

import json
import redis
from log import logger

class Mq():
	def __init__(self, name, host='127.0.0.1', port=6379, password='None'):
		self.__mq = redis.Redis(host=host, port=port, password=password)
		self.__name = name

	def push(self, message):
		str = json.dumps(message.__dict__)
		return int(self.__mq.lpush(self.__name, str))

	def pop(self,timeout=10):
		pop = self.__mq.brpop(self.__name, timeout)
		if pop is None:
			return

		str = pop[1].decode('utf-8')
		return json.loads(str)
