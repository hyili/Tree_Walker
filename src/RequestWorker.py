#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import sys
import requests
import datetime
import threading

from tool import Functions
from tool import Webdriver

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
        if self.config.follow_redirection:
            self.webdriver = Webdriver.ChromeDriver(session.cookies, self.config.verify, self.config.driver_location)
            self.webdriver.init_webdriver()

    def send_head_request(self, session, request):
        return True

    def send_get_request(self, session, config, request, retries=0):
        current_url = ""
        url = ""
        screenshot_PNG = None
        r = None

        try:
            # When this is the first try, make a start time timestamp
            if retries == 0:
                start_time = datetime.datetime.now()

            # Let Webdriver handles the redirection
            url, screenshot_PNG = self.webdriver.run_webdriver(request["url"], request["redirection_timeout"], request["save_screenshot"]) if config.follow_redirection else (request["url"], None)

            # Send request
            r = session.get(url, timeout=request["timeout"], headers=request["header"])

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
                print("RequestWorker(HTTPRequest::send_get_request()): " + str(e))
        except requests.exceptions.Timeout as e:
            status_code = -3
            reason = e
            r = None
            if config.debug_mode:
                print("RequestWorker(HTTPRequest::send_get_request()): " + str(e))
        except requests.exceptions.TooManyRedirects as e:
            status_code = -4
            reason = e
            r = None
            if config.debug_mode:
                print("RequestWorker(HTTPRequest::send_get_request()): " + str(e))
        except requests.exceptions.ConnectionError as e:
            status_code = -5
            reason = e
            r = None
            if config.debug_mode:
                print("RequestWorker(HTTPRequest::send_get_request()): " + str(e))
        except requests.exceptions.InvalidSchema as e:
            status_code = -6
            reason = e
            r = None
            if config.debug_mode:
                print("RequestWorker(HTTPRequest::send_get_request()): " + str(e))
        except Exception as e:
            status_code = -7
            reason = e
            r = None
            if config.debug_mode:
                print("RequestWorker(HTTPRequest::send_get_request()): " + str(e))
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
                query_time = r.elapsed.total_seconds() if r is not None else 0

                return {"sub_url": request["url"], "current_url": current_url, "status_code": status_code, "start_time": start_time, "end_time": end_time, "time_cost": time_cost, "query_time": query_time,"reason": reason, "response": r, "screenshot": screenshot_PNG}
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
        
        if self.config.follow_redirection:
            self.webdriver.close_webdriver()
