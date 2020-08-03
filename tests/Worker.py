#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import sys
import time
import signal
import datetime
import threading
import traceback

import Main
from tool import RequestException

"""
HTTP Request handler 
"""
class HTTPRequestHandler(threading.Thread):
    def __init__(self, thread_id, thread_name, threads, event, request_queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.threads = threads
        # 0: is idling, 1: is running, 2: is reporting
        self.status = 0
        self.event = event
        self.request_queue = request_queue

    def thread_status(self):
        return self.status

    def is_idle(self):
        return self.status == 0

    def is_busy(self):
        return self.status == 1

    def handler(self, request, threads):
        # Record the start timestamp
        start_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H:%M:%S")

        # Call Main to execute the kernel function
        configargs = request

        try:
            Main.handler(configargs=configargs)
        except Exception as e:
            print("Worker(HTTPRequestHandler::handler()): " + str(e))

            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            print("")

        # Do not need to send mail here

    def run(self):
        while not self.event.is_set():
            request = self.request_queue.get()
            if request is None:
                break

            self.status = 1
            self.handler(request, self.threads)
            self.status = 0
