#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import time
import datetime
import threading

from ITRI import ITRIConfigLoader
from ITRI import ITRIOutput
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

    def handler(self, request, threads):
        # Record the start timestamp
        start_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H:%M:%S")

        # Call Main to execute the kernel function
        # TODO: set configargs, json
        configargs = request
        Main.handler(configloader=ITRIConfigLoader.SQL2K5TConfig, configargs=configargs, db_handler=ITRIOutput.db_handler)

        # Do not need to send mail here

    def run(self):
        while not self.event.is_set():
            request = self.request_queue.get()
            if request is None:
                break

            self.status = 1
            self.handler(request, self.threads)
            self.status = 0
