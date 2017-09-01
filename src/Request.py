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
    """
    def send_get_request(self, session, config, request, retries=0):
        link_url = "" #current_url = ""
        r = None
        #print("send_get_request")
        #print(config.timeout)
        try:
            if retries == 0:
                start_time = datetime.datetime.now()
            
            url = Webdriver.run_webdriver(request["url"], request["timeout"], config.driver_location, config.follow_redirection, verify=config.verify)
            r = session.get(url, timeout=request["timeout"], headers=request["header"], verify=config.verify)

            r.encoding = Functions.detect_encoding(r)
            status_code = r.status_code
            reason = r.reason
            link_url=str(r.url)
        #設定例外狀況的status_code
        except requests.exceptions.HTTPError as e:
            status_code = -2
            reason = e
            r = None
            if (config.debug_mode):
                print("Request: "+str(e))
        except requests.exceptions.Timeout as e:
            status_code = -3
            reason = e
            r = None
            if (config.debug_mode):
                print("Request: "+str(e))
        except requests.exceptions.TooManyRedirects as e:
            status_code = -4
            reason = e
            r = None
            if (config.debug_mode):
                print("Request: "+str(e))
        except requests.exceptions.ConnectionError as e:
            status_code = -5
            reason = e
            r = None
            if (config.debug_mode):
                print("Request: "+str(e))
        except requests.exceptions.InvalidSchema as e:
            status_code = -6
            reason = e
            r = None
            if (config.debug_mode):
                print("Request: "+str(e))
        except Exception as e:
            status_code = -7
            reason = e
            r = None
            if (config.debug_mode):
                print("Request: "+str(e))
        finally:
            if status_code in config.broken_link:
                if retries < config.max_retries:
                    if status_code in config.retry_code:
                        #time.sleep(60)
                        response = self.send_get_request(session=session, config=config, request=request, retries=retries+1)
                        r = response
            if retries == 0:
                end_time = datetime.datetime.now()
				#處理時間
                time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0

                return {"link_url": request["url"], "status_code": status_code, "time_cost": time_cost, "reason": reason, "response": r}
            else:
                return r
    """
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
    """
    if history[config.target_url]["status_code"] == 200:
        #print("sss")
        for i in range(0, num_of_worker_threads, 1):
            new_session = copy.deepcopy(session)
            sessions.append(new_session)
            print("182")
            print(GlobalVars.history_in_queue.qsize())
            thread = HTTPRequest(i, str(i), event, new_session, config, GlobalVars.history_in_queue, GlobalVars.history_out_queue)
            thread.start()
            threads.append(thread)
            #print("thread")
            #print(thread)
    """
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