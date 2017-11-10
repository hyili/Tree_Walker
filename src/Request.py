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

import Authenticate
from tool import GlobalVars
from tool import Webdriver
from tool import Functions
from tool import History


"""
Requests TLS Adapter
"""
class TLSAdapter(HTTPAdapter):
    # Deprecated
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1)

"""
Thread class
Worker definition
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
            # When this is the first try, make a start time timestamp
            if retries == 0:
                start_time = datetime.datetime.now()

            # Let Webdriver handles the redirection
            url = Webdriver.run_webdriver(request["url"], request["timeout"], config.driver_location, config.follow_redirection, verify=config.verify)
            # Send request
            r = session.get(url, timeout=request["timeout"], headers=request["header"], verify=config.verify)

            # Set encoding code, then record the result
            r.encoding = Functions.detect_encoding(r)
            status_code = r.status_code
            reason = r.reason
            current_url = str(r.url)
        except requests.exceptions.HTTPError as e:
            status_code = -2
            reason = e
            r = None
            if config.debug_mode:
                print("Request: "+str(e))
        except requests.exceptions.Timeout as e:
            status_code = -3
            reason = e
            r = None
            if config.debug_mode:
                print("Request: "+str(e))
        except requests.exceptions.TooManyRedirects as e:
            status_code = -4
            reason = e
            r = None
            if config.debug_mode:
                print("Request: "+str(e))
        except requests.exceptions.ConnectionError as e:
            status_code = -5
            reason = e
            r = None
            if config.debug_mode:
                print("Request: "+str(e))
        except requests.exceptions.InvalidSchema as e:
            status_code = -6
            reason = e
            r = None
            if config.debug_mode:
                print("Request: "+str(e))
        except Exception as e:
            status_code = -7
            reason = e
            r = None
            if config.debug_mode:
                print("Request: "+str(e))
        finally:
            # If the result status_code is listed in config.search_status, then prepare for retry recursively
            if status_code in config.search_status:
                if retries < config.max_retries:
                    if status_code in config.retry_code:
                        time.sleep(60)
                        response = self.send_get_request(session=session, config=config, request=request, retries=retries+1)
                        r = response

            # Return, and Collect the result here
            if retries == 0:
                end_time = datetime.datetime.now()
                time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0

                return {"sub_url": request["url"], "current_url": current_url, "status_code": status_code, "start_time": start_time, "end_time": end_time, "time_cost": time_cost, "reason": reason, "response": r}
            # If retries is not 0, that means here is still in recursive function
            else:
                return r

    def run(self):
        # Keep running until stop event is set
        while not self.event.is_set():
            # Get a request from q_in queue
            request = self.q_in.get()

            # If request is None, then worker would stop, and break
            if request is None:
                self.q_in.task_done()
                break

            # Send head request first (Some website would expect client send head request first)
            if self.send_head_request(session=self.session, request=request):
                # Output current progress
                if "counter" in request and "total" in request:
                    sys.stderr.write(str(request["counter"])+"/"+str(request["total"])+"\r")

                # Call send_get_request function
                response = self.send_get_request(session=self.session, config=self.config, request=request)

                # Put the result into q_out
                self.q_out.put(response)

            self.q_in.task_done()

"""
Initialize variable
"""
def initialize(config, decode=None):
    global threads, event, sessions, num_of_worker_threads

    # Global variables initialize
    GlobalVars.total_links = 0
    GlobalVars.total_output_links = 0
    GlobalVars.history_out_queue = queue.Queue(2000)
    GlobalVars.history_in_queue = queue.Queue(2000)

    # Thread object (Worker) and session object initialize
    threads = []
    sessions = []
    num_of_worker_threads = config.threshold
    if config.depth == 0:
        num_of_worker_threads = 1
    session = requests.Session()
    #session.mount("https://", TLSAdapter())
    sessions.append(session)
    if config.auth:
        (source, auth_history) = Authenticate.authenticate(session=session, config=config, decode=decode)

    # Disable requests module warnings
    requests.packages.urllib3.disable_warnings()

    # Initialize an event for stopping jobs that parent and children are running
    event = threading.Event()

    # Initialize Worker
    for i in range(0, num_of_worker_threads, 1):
        new_session = copy.deepcopy(session)
        sessions.append(new_session)
        thread = HTTPRequest(i, str(i), event, new_session, config, GlobalVars.history_in_queue, GlobalVars.history_out_queue)
        thread.start()
        threads.append(thread)

"""
Close
"""
def close():
    global sessions, threads, event, num_of_worker_threads

    # Put an None into queue, informing worker to exit
    for i in range(0, num_of_worker_threads, 1):
        GlobalVars.history_in_queue.put(None)

    # Set event for worker
    event.set()

    # Join worker threads
    for thread in threads:
        thread.join()

    # Close sessions
    for session in sessions:
        session.close()

"""
Ctrl + C handler
"""
def signal_handler(signal, frame):

    # Catch SIGINT
    print("Got it!")
    close()
    print("Ready to quit!")
    exit(0)

"""
Navigate into the target website
"""
def navigate(linktexts, config, depth=0, history={}, decode=None):
    links = []
    GlobalVars.total_links += len(linktexts)
    counter = 0

    # Multi-thread version
    # Run through each linktext
    for linktext in linktexts:
        # Using factor_url to complete the linktext, then sub_url records the completed link
        sub_url = Functions.factor_url(config.current_url, linktext[0])
        counter += 1

        # Check if sub_url already exists in history, if so, then update; or create a new one
        if sub_url in history:
            if history[sub_url]["status_code"] in config.search_status:
                GlobalVars.total_output_links += 1

            if config.current_url not in history[sub_url]["parent_url"]:
                history[sub_url]["parent_url"].append(str(config.current_url))

            continue
        else:
            history = History.history_handler(init=True, history=history, url=sub_url, parent_urls=[str(config.current_url)], link_url=str(sub_url), link_name=str(linktext[1]), depth=depth)

        # Put new request into history_in_queue, wait for workers to consume
        GlobalVars.history_in_queue.put({"counter": counter, "total": GlobalVars.total_links, "url": sub_url, "timeout": config.timeout, "header": config.header})

    # When workers processed all the request
    GlobalVars.history_in_queue.join()

    # Keep running until history_out_queue left nothing
    while not GlobalVars.history_out_queue.empty():
        # Get one result from history_out_queue, then update the current history
        result = GlobalVars.history_out_queue.get()
        sub_url = result["sub_url"]
        history = History.history_handler(history=history, url=sub_url, current_url=result["current_url"], status_code=result["status_code"], start_time=result["start_time"], end_time=result["end_time"], time_cost=result["time_cost"], reason=result["reason"])
        r = result["response"]

        # Check if this result page is required to be crawled deeper
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

        # Remove some result that lists in config.ignore_code
        if history[sub_url]["status_code"] in config.ignore_code:
            del history[sub_url]
        else:
            if history[sub_url]["status_code"] in config.search_status:
                GlobalVars.total_output_links += 1

    # Check if recursive depth is reached the maximum depth
    if config.depth == depth:
        return history

    # Run through each links
    for link in links:
        # sub_url is the sub url in current_url page source
        sub_url = link[0]
        # sub_linktexts is the page source of sub_url
        sub_linktexts = Functions.find_linktexts(source=link[1])
        # Set current_url's value to sub_url
        config.current_url = sub_url
        # Update history with the returned result of navigate function
        history.update(navigate(linktexts=sub_linktexts, config=config, depth=depth+1, history=history, decode=decode))

    # Return the result
    return history

