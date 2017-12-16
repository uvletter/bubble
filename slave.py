# -*- coding: utf-8 -*-
import os
import json
import datetime

import requests
import pymongo

from log import logger
from ant import Task, Worker, g

COOKIES=None  # Your Zhihu account cookies.You can get it from the browser developer tools. Or you can set it later.
MONGODB=None  # Your mongodb login url. e.g.'mongodb://username:password@104.207.155.116'. Need to set.

class Topic(object):
	def __init__(self, id, name, children):
		super(Topic, self).__init__()
		self.id = id
		self.name = name
		self.children = children

ant = Worker(__name__)

@ant.crawl('_default')
def collect_topics(task):
	url = 'https://www.zhihu.com/topic/{0}/organize/entire'.format(task.id)
	headers = {'Referer': 'https://www.zhihu.com/topic/{0}/organize/entire'.format(task.id)}
	ant.session.headers.update(headers)
	data = {'_xsrf': ant.session.cookies.get('_xsrf')}
	response = ant.session.post(url, data=data)
	logger.debug('PID {0} {1}'.format(os.getpid(),response.text))
	return response.text

@ant.crawl('load_more')
def load_more(task):
	url = 'https://www.zhihu.com/topic/{0}/organize/entire?child={1}&parent={0}'.format(task.parent, task.child)
	headers = {'Referer': 'https://www.zhihu.com/topic/{0}/organize/entire'.format(task.id)}
	ant.session.headers.update(headers)
	data = {'_xsrf': ant.session.cookies.get('_xsrf')}
	response = ant.session.post(url, data=data)
	logger.debug('PID {0} {1}'.format(os.getpid(),response.text))
	return response.text
		

def _parse(text):
	tree = json.loads(text)
	parent_name = tree['msg'][0][1]
	parent_id = int(tree['msg'][0][2])
	body = tree['msg'][1]
	children=[]

	for pair in body:
		entry = pair[0]
		if entry[0] == 'topic':
			child_id = int(entry[2])
			children.append(child_id)
			parent = g['mongo'].find_one({'_id': parent_id})

			#root node
			if parent is None:
				parent = {'_id': parent_id, 'path': [parent_id]}
				g['mongo'].insert_one(parent) 

			#update topic path info
			path = parent['path']
			path.append(child_id)
			g['mongo'].update_one(
				filter={'_id': child_id},
				update={'$set': {'_id': child_id, 'path': path, 'updatetime': datetime.datetime.now()}},
				upsert=True
			)

			ant.publish_task(Task(id=child_id))
		elif entry[0] == 'load':
			ant.publish_task(Task(0, retry=True, topic='load_more', parent=entry[3],child=entry[2]))

	return Topic(id=parent_id, name=parent_name, children=children)

@ant.parser(collect_topics)
def topic_parser_creater(text):
	topic = _parse(text)
	g['mongo'].update_one(
		filter={'_id': topic.id},
		update={'$set': {'_id': topic.id, 'name': topic.name, 'children':topic.children, 'updatetime': datetime.datetime.now()}},
	)

@ant.parser(load_more)
def topic_parser_appender(text):
	topic = _parse(text)
	g['mongo'].update_one(
		filter={'_id': topic.id},
		update={'$push': {'children': {'$each': topic.children}}, '$set': {'updatetime': datetime.datetime.now()}}
	)

def parse_cookies(text):
	'''A tool function parsing the cookies from raw string to dict'''
	cookies={}
	for line in text.split(';'):     
		name,value=line.strip().split('=',1)  
		cookies[name]=value  
	return cookies

def init_session():
	cookies = COOKIES
	if not cookies:
		cookies = input('Input the login cookies, please.\nYou can look up it on browser developer tool\n')
	cookies = parse_cookies(cookies)
	header = {
		'Host': 'www.zhihu.com',
		'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.',
		'Content-Type': r'application/x-www-form-urlencoded;charset=utf-8',
	}
	return header, cookies

def create_cli(url):
	mongo_cli = pymongo.MongoClient(url, connect=False)
	return mongo_cli.demo.topics

if __name__=='__main__':
	g['mongo'] = create_cli(MONGODB)
	header, cookies = init_session()
	ant.run(5, header=header, cookies=cookies)
