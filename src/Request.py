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

    def send_head_request(self, session, request):
        return True

    def send_get_request(self, session, config, request, retries=0):
        current_url = ""
        r = None

        try:
            if retries == 0:
                start_time = datetime.datetime.now()

            url = Webdriver.run_webdriver(request["url"], request["timeout"], config.driver_location, config.follow_redirection, verify=config.verify)
            r = session.get(url, timeout=request["timeout"], headers=request["header"], verify=config.verify)

            r.encoding = Functions.detect_encoding(r)
            status_code = r.status_code
            reason = r.reason
            current_url = str(r.url)
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
                        time.sleep(60)
                        response = self.send_get_request(session=session, config=config, request=request, retries=retries+1)
                        r = response

            if retries == 0:
                end_time = datetime.datetime.now()
                time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0

                return {"sub_url": request["url"], "current_url": current_url, "status_code": status_code, "time_cost": time_cost, "reason": reason, "response": r}
            else:
                return r

    def run(self):
        while not self.event.is_set():
            request = self.q_in.get()
            if request is None:
                self.q_in.task_done()
                break
            if self.send_head_request(session=self.session, request=request):
                if "counter" in request and "total" in request:
                    sys.stderr.write(str(request["counter"])+"/"+str(request["total"])+"\r")
                response = self.send_get_request(session=self.session, config=self.config, request=request)
                self.q_out.put(response)
            self.q_in.task_done()

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

    GlobalVars.total_links = 0
    GlobalVars.total_output_links = 0
    GlobalVars.history_out_queue = queue.Queue(2000)
    GlobalVars.history_in_queue = queue.Queue(2000)
    threads = []
    sessions = []
    num_of_worker_threads = config.threshold
    if config.depth == 0:
        num_of_worker_threads = 1
    signal.signal(signal.SIGINT, signal_handler)

    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    sessions.append(session)
    (source, history) = Authenticate.authenticate(session=session, config=config, decode=decode)
    linktexts = Functions.find_linktexts(source=source)

    event = threading.Event()
    if history[config.target_url]["status_code"] == 200:
        for i in range(0, num_of_worker_threads, 1):
            new_session = copy.deepcopy(session)
            sessions.append(new_session)
            thread = HTTPRequest(i, str(i), event, new_session, config, GlobalVars.history_in_queue, GlobalVars.history_out_queue)
            thread.start()
            threads.append(thread)

    return (session, history, source, linktexts)

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
def navigate(linktexts, config, depth=1, history={}, decode=None):
    links = []
    total_linktexts = len(linktexts)
    GlobalVars.total_links += total_linktexts
    counter = 0

    if config.multithread:
        for linktext in linktexts:
            sub_url = Functions.factor_url(history[config.current_url]["current_url"], linktext[0])
            counter += 1

            if sub_url in history:
                if history[sub_url]["status_code"] in config.broken_link:
                    history[config.current_url]["contained_broken_link"] += 1
                
                if config.current_url not in history[sub_url]["parent_url"]:
                    history[sub_url]["parent_url"].append(str(config.current_url))

                continue
            else:
                history = History.history_handler(init=True, history=history, url=sub_url, parent_urls=[str(config.current_url)], link_url=str(sub_url), link_name=str(linktext[1]), depth=depth)

            GlobalVars.history_in_queue.put({"counter": counter, "total": total_linktexts, "url": sub_url, "timeout": config.timeout, "header": config.header})

        GlobalVars.history_in_queue.join()

        while not GlobalVars.history_out_queue.empty():
            result = GlobalVars.history_out_queue.get()
            sub_url = result["sub_url"]
            history = History.history_handler(history=history, url=sub_url, current_url=result["current_url"], status_code=result["status_code"], time_cost=result["time_cost"], reason=result["reason"])
            r = result["response"]

            if history[sub_url]["status_code"] == 200:
                if bool(re.search(config.domain_url, history[sub_url]["current_url"])):
                    try:
                        pattern = "text/"
                        if bool(re.search(pattern, r.headers["Content-Type"])):
                            links.append((sub_url, r.text))
                    except Exception as e:
                        if config.debug_mode:
                            print("Request"+str(e))
                        pass

            if history[sub_url]["status_code"] in config.ignore_code:
                del history[sub_url]
            else:
                if history[sub_url]["status_code"] in config.broken_link:
                    history[config.current_url]["contained_broken_link"] += 1

                if history[sub_url]["status_code"] not in config.filter_code:
                    GlobalVars.total_output_links += 1

    else:
        print("Single thread deprecated. Using multithread instead.")
        quit()

    if config.depth == depth:
        return history

    for link in links:
        sub_url = link[0]
        sub_linktexts = Functions.find_linktexts(source=link[1])
        config.current_url = sub_url
        history.update(navigate(linktexts=sub_linktexts, config=config, depth=depth+1, history=history, decode=decode))

    return history

