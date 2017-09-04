#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-
"""
Note: Need to set timeout when parsing the website
"""

import re
import sys
import ssl
import copy
import time
import queue
import signal
import requests
import datetime
import threading

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

import GlobalVars
import Authenticate
from tool import Webdriver
from tool import Functions
from tool import History


"""
Requests TLS Adapter
"""
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1)

"""
Thread class
"""
class HTTPRequest(threading.Thread):
    def __init__(self, thread_id, thread_name, event, session, config, q_in, q_out):
        threading.Thread.__init__(self)
        self.event = event
        self.session = session
        self.config = config
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.q_in = q_in
        self.q_out = q_out
        #print("init")

    def send_head_request(self, session, request):
        return True

    def run(self): 
        print("Request run")
        while not self.event.is_set():
            print("not self.event.is_set()")
            request = self.q_in.get() #history_in_queue沒有變成q_in
            if request is None:
                self.q_in.task_done()
                break
            if self.send_head_request(session=self.session, request=request):
                if "counter" in request and "total" in request:
                    sys.stderr.write(str(request["counter"])+"/"+str(request["total"])+"\r")
                response = self.send_get_request(session=self.session, config=self.config, request=request)
                self.q_out.put(response)
            self.q_in.task_done()
        #else:
            #print("self.event.is_set()")
            #print(self.event.is_set())

"""
Ctrl + C handler
"""
def signal_handler(signal, frame):
    print("Got it!")
    close()
    print("Ready to quit!")
    quit()

"""
Initialize variable
"""
def initialize(config, decode=None):
    global threads, event, sessions, num_of_worker_threads
    #print("2:R.initialize")
    GlobalVars.total_links = 0
    GlobalVars.total_output_links = 0
    GlobalVars.history_out_queue = queue.Queue(2000)
    GlobalVars.history_in_queue = queue.Queue(2000)
    #print("Request.GlobalVars.history_in_queue.qsize()")
    #print(GlobalVars.history_in_queue.qsize()) 
    threads = []
    sessions = []
    num_of_worker_threads = config.threshold
    signal.signal(signal.SIGINT, signal_handler)
    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    sessions.append(session)
    #print("3.session:")
    #print(session)
    (source, history) = Authenticate.authenticate(session=session, config=config, decode=decode)
    print(history)
    #print("break?-no")
    #print(history[config.target_url]["status_code"])
    #"""用途是把history和session放進thread?
    #這段的目的是在?

    event = threading.Event()
    
    return (session, history, source) 

"""
Close
"""
def close():
    global sessions, threads, event, num_of_worker_threads

    for i in range(0, num_of_worker_threads, 1):
        GlobalVars.history_in_queue.put(None)
    event.set()
    for thread in threads:
        thread.join()
    for session in sessions:
        session.close()

"""
Navigate into the target website
"""

def navigate(content_code, config, depth=1, history={}, decode=None): 
    links = []
    counter = 0
    history[config.target_url]["content_code"] = content_code
    return history


def compare_content(source, comparestr): 
    compare_result = ""
    if source != None: 
        if source.find(comparestr)>-1: #比對整份原始碼
            compare_result=0 
        else:
            compare_result=1

    return compare_result