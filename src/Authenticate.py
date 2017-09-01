#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import re
import time
import datetime
import requests

import GlobalVars
from tool.ssllab import ssllabsscanner as ssllabscanner
from tool import History
from tool import Webdriver
from tool import Functions

"""
Authentication class
"""
class Authenticate():
    def __init__(self, session, config, decode):
        self.session = session
        self.config = config
        self.decode = decode
        self.history = None

    def get_session(self):
        return self.session

    def get_history(self):
        return self.history

    def authenticate(self, retries=0):
        
        config = self.config
        self.history = History.history_handler(init=True, history={}, url=config.target_url)
        #print("authenticate.config.timeout:")
        #print(config.timeout)
        r = None
        ssl_grade = "?"
        ssl_report_url = ""

        try:

            if retries == 0:
                start_time = datetime.datetime.now()
            url = config.target_url
            #url = Webdriver.run_webdriver(config.target_url, config.timeout, config.driver_location, config.follow_redirection, config.verify)
            #print("url:")
            print(url)
            #print("authenticate47.config.timeout:")
            #print(config.timeout)
            r = self.session.get(url, timeout=config.timeout, headers=config.header, verify=config.verify)
            #print("authenticate50.r:")
            #print(r)
            if config.auth:
                #print("Au true/")
                if (re.search(config.auth_url_pattern, r.url)):
                    #print("Au herehereyes")
                    r = self.session.post(r.url, timeout=config.timeout, headers=config.header, data=config.payload, verify=True)
                else:
                    #print("Au herehereno")
                    #print(config.auth_url_pattern)
                    #print(r.url)
                    if config.debug_mode:
                        print("It's only for ITRI Single Sign On lol~")
                    self.history = History.history_handler(history=self.history, url=config.target_url, status_code="-9", link_name=config.title, link_url=config.target_url, context = config.context, reason="It's only for ITRI Single Sign On.")
                    quit()
            if config.ssllab_verify:
                ssl_grade = ssllabscanner.newScan(self.config.target_url)["endpoints"][0]["gradeTrustIgnored"]
                ssl_report_url = "https://www.ssllabs.com/ssltest/analyze.html?d="+self.config.target_url
            r.encoding = Functions.detect_encoding(r)
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=r.status_code, link_name=config.title, link_url=config.target_url, context = config.context, reason=r.reason)

            

        except requests.exceptions.HTTPError as e:
            print("requests.exceptions.HTTPError")
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=-2, link_name=config.title, link_url=config.target_url, context = config.context, reason=e)
            r = None
            if (config.debug_mode):
                print("Authenticate: "+str(e))
        except requests.exceptions.Timeout as e:
            print("requests.exceptions.Timeout")
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=-3, link_name=config.title, link_url=config.target_url, context = config.context, reason=e)
            r = None
            if (config.debug_mode):
                print("Authenticate: "+str(e))
        except requests.exceptions.TooManyRedirects as e:
            print("requests.exceptions.TooManyRedirects")
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=-4, link_name=config.title, link_url=config.target_url, context = config.context, reason=e)
            r = None
            if (config.debug_mode):
                print("Authenticate: "+str(e))
        except requests.exceptions.ConnectionError as e:
            print("requests.exceptions.ConnectionError")
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=-5, link_name=config.title, link_url=config.target_url, context = config.context, reason=e)
            r = None
            if (config.debug_mode):
                print("Authenticate: "+str(e))
        except requests.exceptions.InvalidSchema as e:
            print("requests.exceptions.InvalidSchema")
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=-6, link_name=config.title, link_url=config.target_url, context = config.context, reason=e)
            r = None
            if (config.debug_mode):
                print("Authenticate: "+str(e))
        except Exception as e:
            print("Authenticate Exception")
            self.history = History.history_handler(history=self.history, url=config.target_url, status_code=-7, link_name=config.title, link_url=config.target_url, context = config.context, reason=e)
            r = None
            if (config.debug_mode):
                print("Authenticate: "+str(e))

        #這段要再確認清楚retry_code
        finally:
            #print("finally")
            
            if self.history[config.target_url]["status_code"] in config.broken_link:
                if retries < config.max_retries:
                    if self.history[config.target_url]["status_code"] in config.retry_code:
                        config.auth = False
                        time.sleep(60)
                        response = self.authenticate(retries=retries+1)
                        r = response

            if retries == 0:
                end_time = datetime.datetime.now()
                time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
                self.history[config.target_url]["time_cost"] = time_cost
                self.history[config.target_url]["start_time"] = start_time #加入start_time
                #code=200 但時間太久
                #if():
                if(self.history[config.target_url]["status_code"] == 200 and time_cost>float(config.timewarn)):
                    self.history[config.target_url]["status_code"] = "-8"
                    self.history[config.target_url]["reason"] = "time too long"
            return r

"""
Will be forwarded to another authentication page
Then, login with payload information
"""
def authenticate(session, config, decode=None):
    GlobalVars.total_links += 1

    auth = Authenticate(session, config, decode)
    response = auth.authenticate()
    history = auth.get_history()
    ret_val = ("", history)

    if history[config.target_url]["status_code"] == 200:
        try:
            pattern = "text/"
            if bool(re.search(pattern, response.headers["Content-Type"])):
                ret_val = (response.text, history)
        except Exception as e:
            if config.debug_mode:
                print("Authenticate: "+str(e))
            pass

    #if history[config.target_url]["status_code"] in config.ignore_code: #之前把-6忽略 但還是要記錄
        #del history[config.target_url]
    #else:
    if history[config.target_url]["status_code"] not in config.filter_code:
        GlobalVars.total_output_links += 1

    return ret_val

