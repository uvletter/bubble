# -*- coding: utf-8 -*-
import os
import json
import random
import time

from flask import Flask, render_template, send_from_directory, request, abort
import pymongo

MONGODB = None  #  Your mongodb login url. e.g.'mongodb://username:password@104.207.155.116'. Need to set.
COLORS = ['#4f19c7','#c71969','#c71919','#1984c7','#c76919','#8419c7','#c79f19','#c78419','#c719b9','#199fc7','#9f19c7','#69c719','#19c719','#1919c7','#c74f19','#19c7b9','#9fc719','#c7b919','#b9c719','#3419c7','#19b9c7','#34c719','#19c784','#c7199f','#1969c7','#c71984','#1934c7','#84c719','#194fc7','#c7194f','#19c74f','#b919c7','#19c769','#19c79f','#4fc719','#c73419','#19c734','#6919c7','#c71934']
LEVEL = 4
	

def create_cli(url):
	mongo_cli = pymongo.MongoClient(url, connect=False)
	return mongo_cli.demo.topics

app = Flask(__name__)
mongo = create_cli(MONGODB)

def traverse(sets, nodes, edges, id, level):

	#skip duplicate id
	if id in sets:
		return

	root = mongo.find_one({'_id': id})
	if root is None:
		abort(404)
	
	sets[id] = len(sets)	
	root.pop('updatetime')
	root['size'] = 10
	root['color'] = COLORS[random.randint(0, len(COLORS)-1)]
	path = root.pop('path')
	nodes.append(root)

	children = root.pop('children')
	if children is not None and level != 0:
		for child in children:
			edges.append({'src': root['_id'], 'dst': child})
			traverse(sets, nodes, edges, child, level-1)
	return path[-2]

def create_gephi():
	pass

@app.route('/gephi.gexf')
def gephi():
	if not os.path.exists(filepath) or not os.path.isfile(filepath):
		create_gephi();
	return send_from_directory('res', 'gephi.gexf')

@app.route('/search')
def search():
	kw = request.args['kw']
	entity = mongo.find_one({'name': kw})
	if entity is None:
		abort(404)
	return json.dumps({'id' :entity['_id']}),200,{'Content-Type': 'application/json'}

@app.route('/bubble')
@app.route('/bubble/<id>')
def bubble(id=None):
	return render_template('bubble.html')

@app.route('/topic/<int:id>', methods=['GET'])
def topic(id):
	sets = {}
	nodes = []
	edges = []
	parent = traverse(sets, nodes, edges, id, LEVEL)
	jsontext = json.dumps({'parent': parent, 'nodes': nodes, 'edges': [{'src': sets[edge['src']], 'dst':sets[edge['dst']]} for edge in edges]})
	return jsontext, 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
	app.run()