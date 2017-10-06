#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import time
import datetime
import threading

"""
HTTP Request handler 
"""
class HTTPRequestHandler(threading.Thread):
    def __init__(self, thread_id, thread_name, threads, event, send_report_event, request_queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.threads = threads
        # 0: is idling, 1: is running, 2: is reporting
        self.status = 0
        self.event = event
        self.send_report_event = send_report_event
        self.request_queue = request_queue

    def thread_status(self):
        return self.status

    def handler(self, request, threads):
        if request["send_report"]:
            for thread in threads:
                while thread.thread_status() == 1:
                    # TODO:
                    time.sleep(20)

            # Do not need to send mail here
            return
        
        # Record the start timestamp
        start_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H:%M:%S")

        # Call Main to execute the kernel function
        # TODO:
        _record = os.popen("./Main.py commandline --tag "+config.tag+" --url "+request["url"]+" --depth "+request["level"]+" --title \""+request["title"]+"\" --email \""+request["mailto"]+"\" --unit \""+request["unit"]+"\" --filename \"APILog\" --description \""+request["empno"]+"\"")
        record = _record.read().replace("\n", "")

        # Make sure that Main.py returns only status code
        try:
            record = int(record)
        except Exception as e:
            # TODO:
            if config.debug_mode:
                print("APIServer: "+str(e))
            print("Something wrong here.")
            exit(0)

        # Do not need to send mail here

        _record.close()

    def run(self):
        while not self.event.is_set():
            request = self.request_queue.get()
            if request is None:
                break

            if request["send_report"]:
                self.send_report_event.set()
                self.status = 2

                self.handler(request, self.threads)

                self.status = 0
                self.send_report_event.clear()
            else:
                while self.send_report_event.is_set():
                    # TODO:
                    time.sleep(20)
                    pass

                self.status = 1

                self.handler(request, self.threads)

                self.status = 0
