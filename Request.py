#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note: Need to set timeout when parsing the website
"""

import requests
import urllib.parse
import html.parser
import os
import signal
import re
import configparser
import datetime
import sys
from lxml import etree
import csv
import threading
import queue
import copy
from selenium import webdriver
from bs4 import BeautifulSoup

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl

"""
Global variable
- total_links
    - this is used to record the total number of parsed links.
- total_output_links
    - this is used to record the total number of parsed links that are NOT in
    filter_code.
- history_out_queue
    - this is the message queue from worker thread to main thread to transfer history contains.
- history_in_queue
    - this is the message queue from main thread to worker thread to transfer history inputs.
"""

"""
Requests TLS Adapter
"""
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1)

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

    def authenticate(self, retries=1):
        config = self.config
        self.history = history_handler(init=True, url=self.config.target_url)
        r = None

        try:
            start_time = datetime.datetime.now()
            url = run_webdriver(config.target_url, config.timeout, config.driver_location, config.follow_redirection, config.verify)
            r = self.session.get(url, timeout=config.timeout, headers=config.header, verify=config.verify)

            if config.auth:
                r = self.session.post(r.url, timeout=config.timeout, headers=config.header, data=config.payload, verify=True)

            r.encoding = detect_encoding(r)
            self.history = history_handler(history=self.history, url=config.target_url, current_url=r.url, status_code=r.status_code, link_name=config.title, link_url=config.target_url, admin_email=config.email, admin_unit=config.unit, reason=r.reason, depth=0)
        except requests.exceptions.HTTPError as e:
            self.history = history_handler(history=self.history, url=config.target_url, status_code=-2, link_name=config.title, admin_email=config.email, link_url=config.target_url, admin_unit=config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.Timeout as e:
            self.history = history_handler(history=self.history, url=config.target_url, status_code=-3, link_name=config.title, admin_email=config.email, link_url=config.target_url, admin_unit=config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.TooManyRedirects as e:
            self.history = history_handler(history=self.history, url=config.target_url, status_code=-4, link_name=config.title, admin_email=config.email, link_url=config.target_url, admin_unit=config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.ConnectionError as e:
            self.history = history_handler(history=self.history, url=config.target_url, status_code=-5, link_name=config.title, admin_email=config.email, link_url=config.target_url, admin_unit=config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.InvalidSchema as e:
            self.history = history_handler(history=self.history, url=config.target_url, status_code=-6, link_name=config.title, admin_email=config.email, link_url=config.target_url, admin_unit=config.unit, reason=e, depth=0)
            r = None
        except Exception as e:
            self.history = history_handler(history=self.history, url=config.target_url, status_code=-7, link_name=config.title, admin_email=config.email, link_url=config.target_url, admin_unit=config.unit, reason=e, depth=0)
            r = None
        finally:
            if self.history[config.target_url]["status_code"] in config.broken_link:
                if retries < config.max_retries:
                    response = self.authenticate(retries=retries+1)
                    return response
            end_time = datetime.datetime.now()
            time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
            self.history[config.target_url]["time_cost"] = time_cost

            return r

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
            start_time = datetime.datetime.now()
            url = run_webdriver(request["url"], request["timeout"], config.driver_location, config.follow_redirection, verify=config.verify)
            r = session.get(url, timeout=request["timeout"], headers=request["header"], verify=config.verify)

            r.encoding = detect_encoding(r)
            status_code = r.status_code
            reason = r.reason
            current_url = str(r.url)
        except requests.exceptions.HTTPError as e:
            status_code = -2
            reason = e
            r = None
        except requests.exceptions.Timeout as e:
            status_code = -3
            reason = e
            r = None
        except requests.exceptions.TooManyRedirects as e:
            status_code = -4
            reason = e
            r = None
        except requests.exceptions.ConnectionError as e:
            status_code = -5
            reason = e
            r = None
        except requests.exceptions.InvalidSchema as e:
            status_code = -6
            reason = e
            r = None
        except Exception as e:
            status_code = -7
            reason = e
            r = None
        finally:
            if status_code in config.broken_link:
                if retries < config.max_retries:
                    response = self.send_get_request(session=session, config=config, request=request, retries=retries+1)
                    return response
            end_time = datetime.datetime.now()
            time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0

            return {"sub_url": request["url"], "current_url": current_url, "status_code": status_code, "time_cost": time_cost, "reason": reason, "response": r}

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
Config class
"""
class Config():
    def __init__(self, tag, filename):
        self.tag = tag
        self.filename = filename
        self.title = ""
        self.email = ""
        self.unit = ""

    def load(self, conf, tag, option, funct=None):
        try:
            result = conf.get(tag, option)
        except configparser.NoSectionError as e:
            print(e)
            quit()
        except:
            try:
                result = conf.get("DEFAULT", option)
            except:
                quit()

        if funct is None:
            return result
        else:
            return funct(result)

    def load_config(self):
        conf = configparser.ConfigParser()
        conf.read(self.filename)
        conf.sections()

        _auth = self.load(conf, self.tag, "AUTH")
        _multithread = self.load(conf, self.tag, "MULTITHREAD")
        _threshold = self.load(conf, self.tag, "THRESHOLD", int)
        _print_depth = self.load(conf, self.tag, "PRINT_DEPTH")
        _target_url = self.load(conf, self.tag, "TARGET_URL")
        _current_url = _target_url
        _user = self.load(conf, self.tag, "USER")
        _password = self.load(conf, self.tag, "PASS")
        _header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36"}
        _depth = self.load(conf, self.tag, "DEPTH", int)
        _timeout = self.load(conf, self.tag, "TIMEOUT", int)
        _domain_url = self.load(conf, self.tag, "DOMAIN_URL", pattern_generator)
        _filter_code = self.load(conf, self.tag, "FILTER")
        _broken_link = self.load(conf, self.tag, "BROKEN_LINK")
        _max_retries = self.load(conf, self.tag, "MAX_RETRIES", int)
        _output_format = self.load(conf, self.tag, "FORMAT")
        _sort = self.load(conf, self.tag, "SORT")
        _follow_redirection = self.load(conf, self.tag, "FOLLOW_REDIRECTION")
        _driver_location = self.load(conf, self.tag, "DRIVER_LOCATION")
        _verify = self.load(conf, self.tag, "VERIFY_CERTIFICATE")

        if _auth == "YES":
            self.auth = True
        else:
            self.auth = False
        if _multithread == "YES":
            self.multithread = True
        else:
            self.multithread = False
        self.threshold = _threshold
        self.print_depth = [int(i) for i in _print_depth.split(",")]
        self.target_url = factor_url(_target_url, "")
        self.current_url = _current_url
        self.user = _user
        self.password = _password
        self.header = _header
        if self.auth:
            self.payload = {"USER": self.user, "PASSWORD": self.password}
        else:
            self.payload = {}
        self.depth = _depth
        self.timeout = _timeout
        self.domain_url = _domain_url
        self.filter_code = [int(i) for i in _filter_code.split(",")]
        self.broken_link = [int(i) for i in _broken_link.split(",")]
        self.max_retries = _max_retries
        self.output_format = [str(i) for i in _output_format.split(",")]
        self.sort = _sort
        if _follow_redirection == "YES":
            self.follow_redirection = True
        else:
            self.follow_redirection = False
        self.driver_location = _driver_location
        if _verify == "YES":
            self.verify = True
        else:
            self.verify = False

"""
Ctrl + C handler
"""
def signal_handler(signal, frame):
    close()
    quit()

"""
Initialize variable
"""
def initialize(config, decode=None):
    global total_links, total_output_links, history_out_queue, history_in_queue, threads, event, sessions, num_of_worker_threads

    total_links = 0
    total_output_links = 0
    history_out_queue = queue.Queue(2000)
    history_in_queue = queue.Queue(2000)
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
    (source, history) = authenticate(session=session, config=config, decode=decode)
    linktexts = find_linktexts(source=source)

    event = threading.Event()
    if history[config.target_url]["status_code"] == 200:
        for i in range(0, num_of_worker_threads, 1):
            new_session = copy.deepcopy(session)
            sessions.append(new_session)
            thread = HTTPRequest(i, str(i), event, new_session, config, history_in_queue, history_out_queue)
            thread.start()
            threads.append(thread)

    return (session, history, source, linktexts)

"""
Close
"""
def close():
    global sessions, threads, event, num_of_worker_threads, history_in_queue

    for i in range(0, num_of_worker_threads, 1):
        history_in_queue.put(None)
    event.set()
    for thread in threads:
        thread.join()
    for session in sessions:
        session.close()

"""
Encoding detection
"""
def detect_encoding(r):
    content1 = None
    content2 = None
    header = None

    try:
        contentsoup = BeautifulSoup(r.content.decode("utf-8", "ignore"), "lxml")
        pattern = re.compile("charset=([0-9A-Za-z\-]+)")

        metatag = contentsoup.select("meta[charset]")
        for linktext in metatag:
            content1 = str(linktext["charset"]).lower()

        metatag = contentsoup.select('meta[content*="charset="]')
        for linktext in metatag:
            content2 = str(re.findall(pattern, linktext["content"])[0]).lower()

        header = requests.utils.get_encoding_from_headers(r.headers)

        if content1 is not None:
            return content1
        elif content2 is not None:
            return content2
        else:
            return header
    except:
        return None

"""
history handler
"""
def history_handler(init=False, history={}, url="", parent_urls=[], link_url="", link_name="", current_url="", status_code=-1, contained_broken_link=0, admin_email="", admin_unit="", time_cost=-1, reason="", depth=-1):
    if url == "" or history is None:
        print("History update failed.")
        return history

    if init:
        history[url] = {}
        history[url]["parent_url"] = parent_urls
        history[url]["link_url"] = link_url
        history[url]["link_name"] = link_name
        history[url]["current_url"] = current_url
        history[url]["status_code"] = status_code
        history[url]["contained_broken_link"] = contained_broken_link
        history[url]["admin_email"] = admin_email
        history[url]["admin_unit"] = admin_unit
        history[url]["time_cost"] = time_cost
        history[url]["reason"] = reason
        history[url]["depth"] = depth
    else:
        if url not in history:
            history_handler(init=True, history=history, url=url)
        for parent_url in parent_urls:
            if parent_url not in history[url]["parent_url"]:
                history[url]["parent_url"].append(parent_url)
        if link_url != "":
            history[url]["link_url"] = link_url
        if link_name != "":
            history[url]["link_name"] = link_name
        if current_url != "":
            history[url]["current_url"] = current_url
        if status_code != -1:
            history[url]["status_code"] = status_code
        if contained_broken_link != 0:
            history[url]["contained_broken_link"] = contained_broken_link
        if admin_email != "":
            history[url]["admin_email"] = admin_email
        if admin_unit != "":
            history[url]["admin_unit"] = admin_unit
        if time_cost != -1:
            history[url]["time_cost"] = time_cost
        if reason != "":
            history[url]["reason"] = reason
        if depth != -1:
            history[url]["depth"] = depth

    return history

"""
- Selenium Web Driver
    - just use selenium for web url after redirecting
"""
def run_webdriver(url, timeout, driver_location="/usr/local/bin/phantomjs", follow_redirection=False, verify=False):
    if not follow_redirection:
        return url

    # Authentication session synchronization between requests and selenium problem. TODO:
    wd = webdriver.PhantomJS(executable_path=driver_location, service_args=["--ignore-ssl-errors="+str(not verify).lower(), "--ssl-protocol=any"])
    # wd = webdriver.Chrome(executable_path="/Users/hyili/Documents/Python/selenium/ChromeDriver/chromedriver")
    wd.set_page_load_timeout(timeout)
    wd.set_script_timeout(timeout)
    try:
        wd.get(url)
        result = wd.current_url
        if wd.current_url == "about:blank":
            result = url
    except:
        result = url
    finally:
        wd.close()
        return result

"""
Navigate into the target website
"""
def navigate(linktexts, config, depth=1, history={}, decode=None):
    global total_links, total_output_links, history_out_queue, history_in_queue

    links = []
    total_linktexts = len(linktexts)
    total_links += total_linktexts
    counter = 0

    if config.multithread:
        for linktext in linktexts:
            sub_url = factor_url(history[config.current_url]["current_url"], linktext[0])
            counter += 1

            if sub_url in history:
                if history[sub_url]["status_code"] in config.broken_link:
                    history[config.current_url]["contained_broken_link"] += 1

                if config.current_url not in history[sub_url]["parent_url"]:
                    history[sub_url]["parent_url"].append(str(config.current_url))

                continue
            else:
                history = history_handler(history=history, url=sub_url, parent_urls=[str(config.current_url)], link_url=str(sub_url), link_name=str(linktext[1]), depth=depth)

            history_in_queue.put({"counter": counter, "total": total_linktexts, "url": sub_url, "timeout": config.timeout, "header": config.header})

        history_in_queue.join()

        while not history_out_queue.empty():
            result = history_out_queue.get()
            sub_url = result["sub_url"]
            history = history_handler(history=history, url=sub_url, current_url=result["current_url"], status_code=result["status_code"], time_cost=result["time_cost"], reason=result["reason"])
            r = result["response"]

            if history[sub_url]["status_code"] == 200:
                if bool(re.search(config.domain_url, history[sub_url]["current_url"])):
                    try:
                        pattern = "text/"
                        if bool(re.search(pattern, r.headers["Content-Type"])):
                            links.append((sub_url, r.text))
                    except:
                        pass

            if history[sub_url]["status_code"] in config.broken_link:
                history[config.current_url]["contained_broken_link"] += 1

            if history[sub_url]["status_code"] in [-6]:
                del history[sub_url]
    else:
        print("Single thread deprecated. Using multithread instead.")
        quit()

    if config.depth == depth:
        return history

    for link in links:
        sub_url = link[0]
        sub_linktexts = find_linktexts(source=link[1])
        config.current_url = sub_url
        history.update(navigate(linktexts=sub_linktexts, config=config, depth=depth+1, history=history, decode=decode))

    return history

"""
Reformat url
"""
def factor_url(current_url, sub_url):
    pattern = "^(javascript|tel):"
    if bool(re.search(pattern, sub_url)):
        return sub_url

    sub_url = html.parser.HTMLParser().unescape(sub_url)
    current_url = current_url.strip()
    sub_url = sub_url.strip()

    pattern = "^(ftp|http(s)?)://"
    if bool(re.search(pattern, sub_url)):
        url = sub_url
    else:
        url = urllib.parse.urljoin(current_url, sub_url)

    ret_val = urllib.parse.urlsplit(url).geturl()
    return ret_val

"""
Will be forwarded to another authentication page
Then, login with payload information
"""
def authenticate(session, config, decode=None):
    global total_links, total_output_links

    total_links += 1

    auth = Authenticate(session, config, decode)
    response = auth.authenticate()
    history = auth.get_history()

    if history[config.target_url]["status_code"] not in config.filter_code:
        total_output_links += 1

    ret_val = ("", history)
    if history[config.target_url]["status_code"] == 200:
        try:
            pattern = "text/"
            if bool(re.search(pattern, response.headers["Content-Type"])):
                ret_val = (response.text, history)
        except:
            pass
        finally:
            return ret_val

    return ret_val

"""
Find all the link in the given source
"""
def find_linktexts(source):
    linktexts = []
    soup = BeautifulSoup(source, "lxml")
    atag = soup.select("a[href]")
    for linktext in atag:
        if linktext.string is None:
            linktexts.append((linktext["href"], ""))
        else:
            linktexts.append((linktext["href"], linktext.string))

    return linktexts

"""
Output file generator using specified format
"""
def file_generator(history, logger, config, output_filename):
    global total_links, total_output_links

    directory = "output/"
    output_filename = output_filename.replace("/", " ")
    if total_output_links > 0:
        logger.warn("["+config.tag+"] filter_code: {"+str(config.filter_code)+"}, print_depth: {"+str(config.print_depth)+"} Generating "+output_filename+"...")
    if "XML" in config.output_format:
        if config.sort == "URL":
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(total_links))
            total_output_link = etree.SubElement(time, "total_output_links")
            total_output_link.set("value", str(total_output_links))
            for log in history:
                if history[log]["depth"] not in config.print_depth:
                    continue
                if history[log]["status_code"] not in config.filter_code or history[log]["contained_broken_link"] != 0:
                    locate = etree.SubElement(time, "locate")
                    locate.set("value", log)
                    try:
                        parent_url = etree.SubElement(locate, "parent_url")
                        parent_url.set("value", str(history[log]["parent_url"]))
                        link_url = etree.SubElement(locate, "link_url")
                        link_url.set("value", str(history[log]["link_url"]))
                        link_name = etree.SubElement(locate, "link_name")
                        link_name.set("value", str(history[log]["link_name"]))
                        current_url = etree.SubElement(locate, "current_url")
                        current_url.set("value", str(history[log]["current_url"]))
                        status_code = etree.SubElement(locate, "status_code")
                        status_code.set("value", str(history[log]["status_code"]))
                        contained_broken_link = etree.SubElement(locate, "contained_broken_link")
                        contained_broken_link.set("value", str(history[log]["contained_broken_link"]))
                        admin_email = etree.SubElement(locate, "admin_email")
                        admin_email.set("value", str(history[log]["admin_email"]))
                        admin_unit = etree.SubElement(locate, "admin_unit")
                        admin_unit.set("value", str(history[log]["admin_unit"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(history[log]["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(history[log]["reason"]))
                    except Exception as e:
                        print(e)
                        continue
            tree = etree.ElementTree(time)
            with open(directory+output_filename+".xml", "ab") as xmlfile:
                tree.write(xmlfile, pretty_print=True)
                xmlfile.close()
        elif config.sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(total_links))
            total_output_link = etree.SubElement(time, "total_output_links")
            total_output_link.set("value", str(total_output_links))
            for log in sort_by_status:
                if log["depth"] not in config.print_depth:
                    continue
                if log["status_code"] not in config.filter_code or log["contained_broken_link"] != 0:
                    locate = etree.SubElement(time, "locate")
                    locate.set("value", log["link_url"])
                    try:
                        parent_url = etree.SubElement(locate, "parent_url")
                        parent_url.set("value", str(log["parent_url"]))
                        link_url = etree.SubElement(locate, "link_url")
                        link_url.set("value", str(log["link_url"]))
                        link_name = etree.SubElement(locate, "link_name")
                        link_name.set("value", str(log["link_name"]))
                        current_url = etree.SubElement(locate, "current_url")
                        current_url.set("value", str(log["current_url"]))
                        status_code = etree.SubElement(locate, "status_code")
                        status_code.set("value", str(log["status_code"]))
                        contained_broken_link = etree.SubElement(locate, "contained_broken_link")
                        contained_broken_link.set("value", str(log["contained_broken_link"]))
                        admin_email = etree.SubElement(locate, "admin_email")
                        admin_email.set("value", str(log["admin_email"]))
                        admin_unit = etree.SubElement(locate, "admin_unit")
                        admin_unit.set("value", str(log["admin_unit"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(log["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(log["reason"]))
                    except Exception as e:
                        print(e)
                        continue
            tree = etree.ElementTree(time)
            with open(directory+output_filename+".xml", "ab") as xmlfile:
                tree.write(xmlfile, pretty_print=True)
                xmlfile.close()

    if "CSV" in config.output_format:
        file_exist = False
        if os.path.isfile(directory+output_filename+".csv"):
            file_exist = True

        if config.sort == "URL":
            with open(directory+output_filename+".csv", "a") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "共印出幾條網址", "共掃過幾條網址"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exist:
                    writer.writeheader()
                for log in history:
                    if history[log]["depth"] not in config.print_depth:
                        continue
                    if history[log]["status_code"] not in config.filter_code or history[log]["contained_broken_link"] != 0:
                        try:
                            writer.writerow({"日期時間": date_time, "從何而來": str(history[log]["parent_url"]), "連結網址": str(history[log]["link_url"]), "連結名稱": str(history[log]["link_name"]), "當前網址": str(history[log]["current_url"]), "狀態碼": str(history[log]["status_code"]), "第一層失連數": str(history[log]["contained_broken_link"]), "負責人email": str(history[log]["admin_email"]), "負責人單位": str(history[log]["admin_unit"]), "花費時間": str(history[log]["time_cost"]), "原因": str(history[log]["reason"])})
                        except Exception as e:
                            print(e)
                            continue
                if config.depth != 0:
                    pass
                csvfile.close()
        elif config.sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            with open(directory+output_filename+".csv", "a") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "共印出幾條網址", "共掃過幾條網址"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exist:
                    writer.writeheader()
                for log in sort_by_status:
                    if log["depth"] not in config.print_depth:
                        continue
                    if log["status_code"] not in config.filter_code or log["contained_broken_link"] != 0:
                        try:
                            writer.writerow({"日期時間": date_time, "從何而來": str(log["parent_url"]), "連結網址": str(log["link_url"]), "連結名稱": str(log["link_name"]), "當前網址": str(log["current_url"]), "狀態碼": str(log["status_code"]), "第一層失連數": str(log["contained_broken_link"]), "負責人email": str(log["admin_email"]), "負責人單位": str(log["admin_unit"]), "花費時間": str(log["time_cost"]), "原因": str(log["reason"])})
                        except Exception as e:
                            print(e)
                            continue
                if config.depth != 0:
                    pass
                csvfile.close()

    if "JSON" in config.output_format:
        pass
    if "STDOUT" in config.output_format:
        print("\n"+str(history[config.target_url]["status_code"]))

"""
transform the target_url to domain_url in regular expression format
"""
def pattern_generator(target_url):
    domain_url = target_url

    domain_url = re.sub("\.", "\\.", domain_url)
    domain_url = re.sub("\:", "\\:", domain_url)
    domain_url = re.sub("\?", "\\?", domain_url)
    domain_url = re.sub("\*", "\\*", domain_url)
    domain_url = re.sub("\+", "\\+", domain_url)
    domain_url = re.sub("\^", "\\^", domain_url)
    domain_url = re.sub("\$", "\\$", domain_url)
    domain_url = re.sub("\~", "\\~", domain_url)
    domain_url = re.sub("\(", "\\(", domain_url)
    domain_url = re.sub("\)", "\\)", domain_url)
    domain_url = re.sub("\[", "\\[", domain_url)
    domain_url = re.sub("\]", "\\]", domain_url)
    domain_url = re.sub("\{", "\\{", domain_url)
    domain_url = re.sub("\}", "\\}", domain_url)
    domain_url = re.sub("\|", "\\|", domain_url)
    domain_url = re.sub("\&", "\\&", domain_url)

    return domain_url
