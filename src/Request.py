#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import re
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
import RequestWorker
from tool import GlobalVars
from tool import Functions
from tool import History


class Request():
    """
    Requests TLS Adapter
    """
    class TLSAdapter(HTTPAdapter):
        # Deprecated
        def init_poolmanager(self, connections, maxsize, block=False):
            self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1)
    
    """
    Initialize variable
    """
    def __init__(self, config, decode=None):
        # Global variables initialize
        GlobalVars.total_links = 0
        GlobalVars.total_output_links = 0
        self.history_out_queue = queue.Queue(2000)
        self.history_in_queue = queue.Queue(2000)
        self.config = config
        self.decode = decode
    
        # Thread object (Worker) and session object initialize
        self.threads = []
        self.sessions = []
        self.num_of_worker_threads = config.threshold
        if config.depth == 0:
            self.num_of_worker_threads = 1
        session = requests.Session()
        #session.mount("https://", TLSAdapter())
        self.sessions.append(session)
        if config.auth:
            (source, auth_history) = Authenticate.authenticate(session=session, config=config, decode=decode)
            if source == "":
                config.sso_check = False
            if source == None:
                raise Exception("Request: SSO failed")
    
        # Disable requests module warnings
        requests.packages.urllib3.disable_warnings()
    
        # Initialize an event for stopping jobs that parent and children are running
        self.event = threading.Event()
    
        # Initialize Worker
        for i in range(0, self.num_of_worker_threads, 1):
            # TODO: fetch out the cookies
            new_session = copy.deepcopy(session)
            self.sessions.append(new_session)
            thread = RequestWorker.HTTPRequest(i, str(i), self.event, new_session, config, self.history_in_queue, self.history_out_queue)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
    
    """
    Close
    """
    def close(self):
        # Put an None into queue, informing worker to exit
        for i in range(0, self.num_of_worker_threads, 1):
            self.history_in_queue.put(None)
    
        # Set event for worker
        self.event.set()
    
        # Join worker threads
        for thread in self.threads:
            thread.join()
    
        # Close sessions
        for session in self.sessions:
            session.close()
    
    """
    Ctrl + C handler
    """
    def signal_handler(self, signal, frame):
    
        # Catch SIGINT
        print("Got it!")
        self.close()
        print("Ready to quit!")
        exit(0)
    
    """
    Navigate into the target website
    """
    def navigate(self, linktexts, config, depth=0, history={}, decode=None):
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
    
            # Put new request into self.history_in_queue, wait for workers to consume
            self.history_in_queue.put({"counter": counter, "total": GlobalVars.total_links, "url": sub_url, "timeout": config.timeout, "redirection_timeout": config.redirection_timeout, "header": config.header, "save_screenshot": config.save_screenshot})
    
        # When workers processed all the request
        self.history_in_queue.join()
    
        # Keep running until self.history_out_queue left nothing
        while not self.history_out_queue.empty():
            # Get one result from self.history_out_queue, then update the current history
            result = self.history_out_queue.get()
            sub_url = result["sub_url"]
            r = result["response"]
    
            context_found = Functions.find_context(r.text, config.context) if r is not None else False
    
            history = History.history_handler(history=history, url=sub_url, current_url=result["current_url"], status_code=result["status_code"], start_time=result["start_time"], end_time=result["end_time"], time_cost=result["time_cost"], query_time=result["query_time"], reason=result["reason"], context_found=context_found, screenshot=result["screenshot"])
    
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
            history.update(self.navigate(linktexts=sub_linktexts, config=config, depth=depth+1, history=history, decode=decode))
    
        # Return the result
        return history
    
