# -*- coding: utf-8 -*-
from ant import Queen, Task

ant = Queen(__name__)

if __name__=='__main__':
	rootid = 19776749 #root topic id
	ant.run(Task(id=rootid))

