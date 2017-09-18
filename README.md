# bubble
### Usage
Be sure you have installed Python3, pip and virtualenv in you computer, then
```sh
git clone https://github.com/ElevenKeys/bubble.git
cd bubble
virtualenv env
source env/bin/activate
pip3 install -r requirements.txt
```
Now the environment is OK.   

Configure the micro in the header of ant.py, slave.py and bubble.py, including the IP and anthentication of the Redis and MongoDB server, and the cookies of Zhihu anthentication.   

If you want to crawl the topics of Zhihu, just run the master.py and slave.py in the background, waiting for several hours and the topic data wll be collected and stored in MongoDB.   

If you want to see the topic presentation,   
```sh
export FLASK_APP=bubble.py
flask run
```
visit the page in http://localhost:5000/bubble, and search your interesting topic.  

This is the impression website [bubbles](http://104.207.152.166/bubble/19580349). 