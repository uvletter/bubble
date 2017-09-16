# -*- coding: utf-8 -*-
import os
import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)
  
cwd = os.path.abspath(os.path.dirname(__file__))
logpath = os.path.join(cwd, 'log')
if not os.path.exists(logpath):
	os.mkdir(logpath)
logfile = os.path.join(logpath,'logger.txt')
file = logging.FileHandler(logfile, mode='a')  
console = logging.StreamHandler()  
  
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s\r\n")  
file.setFormatter(formatter)  
console.setFormatter(formatter)  
  
logger.addHandler(file)  
logger.addHandler(console) 