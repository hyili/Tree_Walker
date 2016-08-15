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
        self.max_retries = 3
        self.history = None

    def get_session(self):
        return self.session

    def get_history(self):
        return self.history

    def authenticate(self, retries=1):
        self.history = history_handler(init=True, url=self.config.target_url)
        r = None

        try:
            start_time = datetime.datetime.now()
            url = run_webdriver(self.config.target_url, self.config.timeout, self.config.follow_redirection, self.config.verify)
            r = self.session.get(url, timeout=self.config.timeout, headers=self.config.header, verify=self.config.verify)

            if self.config.auth:
                r = self.session.post(r.url, timeout=self.config.timeout, headers=self.config.header, data=self.config.payload, verify=True)

            r.encoding = detect_encoding(r)
            self.history = history_handler(history=self.history, url=self.config.target_url, current_url=r.url, status_code=r.status_code, link_name=self.config.title, link_url=self.config.target_url, admin_email=self.config.email, admin_unit=self.config.unit, reason=r.reason, depth=0)
        except requests.exceptions.HTTPError as e:
            self.history = history_handler(history=self.history, url=self.config.target_url, status_code=-2, link_name=self.config.title, admin_email=self.config.email, link_url=self.config.target_url, admin_unit=self.config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.Timeout as e:
            if retries < self.max_retries:
                response = self.authenticate(retries=retries+1)
                return response
            else:
                self.history = history_handler(history=self.history, url=self.config.target_url, status_code=-3, link_name=self.config.title, admin_email=self.config.email, link_url=self.config.target_url, admin_unit=self.config.unit, reason=e, depth=0)
                r = None
        except requests.exceptions.TooManyRedirects as e:
            self.history = history_handler(history=self.history, url=self.config.target_url, status_code=-4, link_name=self.config.title, admin_email=self.config.email, link_url=self.config.target_url, admin_unit=self.config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.ConnectionError as e:
            self.history = history_handler(history=self.history, url=self.config.target_url, status_code=-5, link_name=self.config.title, admin_email=self.config.email, link_url=self.config.target_url, admin_unit=self.config.unit, reason=e, depth=0)
            r = None
        except requests.exceptions.InvalidSchema as e:
            self.history = history_handler(history=self.history, url=self.config.target_url, status_code=-6, link_name=self.config.title, admin_email=self.config.email, link_url=self.config.target_url, admin_unit=self.config.unit, reason=e, depth=0)
            r = None
        except Exception as e:
            self.history = history_handler(history=self.history, url=self.config.target_url, status_code=-7, link_name=self.config.title, admin_email=self.config.email, link_url=self.config.target_url, admin_unit=self.config.unit, reason=e, depth=0)
            r = None
        finally:
            end_time = datetime.datetime.now()
            time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
            self.history[self.config.target_url]["time_cost"] = time_cost

            return r

"""
Thread class
"""
class HTTPRequest(threading.Thread):
    def __init__(self, thread_id, thread_name, event, session, verify, follow_redirection, q_in, q_out):
        threading.Thread.__init__(self)
        self.event = event
        self.session = session
        self.verify = verify
        self.follow_redirection = follow_redirection
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.q_in = q_in
        self.q_out = q_out
        self.max_retries = 3

    def send_head_request(self, session, request):
        return True

    def send_get_request(self, session, request, retries=0, follow_redirection=False, verify=False):
        current_url = ""
        r = None

        try:
            start_time = datetime.datetime.now()
            url = run_webdriver(request["url"], request["timeout"], follow_redirection, verify=verify)
            r = session.get(url, timeout=request["timeout"], headers=request["header"], verify=verify)

            r.encoding = detect_encoding(r)
            status_code = r.status_code
            reason = r.reason
            current_url = str(r.url)
        except requests.exceptions.HTTPError as e:
            status_code = -2
            reason = e
            r = None
        except requests.exceptions.Timeout as e:
            if retries < self.max_retries:
                response = self.send_get_request(session=session, request=request, retries=retries+1, follow_redirection=follow_redirection, verify=verify)
                return response
            else:
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
                response = self.send_get_request(session=self.session, request=request, follow_redirection=self.follow_redirection, verify=self.verify)
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
        if _auth == "YES":
            self.auth = True
        else:
            self.auth = False
        _multithread = self.load(conf, self.tag, "MULTITHREAD")
        if _multithread == "YES":
            self.multithread = True
        else:
            self.multithread = False
        self.threshold = self.load(conf, self.tag, "THRESHOLD", int)
        print_depths = self.load(conf, self.tag, "PRINT_DEPTH")
        self.print_depth = [int(i) for i in print_depths.split(",")]
        self.target_url = factor_url(self.load(conf, self.tag, "TARGET_URL"), "")
        self.current_url = self.target_url
        self.user = self.load(conf, self.tag, "USER")
        self.password = self.load(conf, self.tag, "PASS")
        self.header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36"}
        if self.auth:
            self.payload = {"USER": self.user, "PASSWORD": self.password}
        else:
            self.payload = {}
        self.depth = self.load(conf, self.tag, "DEPTH", int)
        self.timeout = self.load(conf, self.tag, "TIMEOUT", int)
        self.domain_url = self.load(conf, self.tag, "DOMAIN_URL", pattern_generator)
        filter_codes = self.load(conf, self.tag, "FILTER")
        self.filter_code = [int(i) for i in filter_codes.split(",")]
        output_formats = self.load(conf, self.tag, "FORMAT")
        self.output_format = [str(i) for i in output_formats.split(",")]
        self.sort = self.load(conf, self.tag, "SORT")
        _follow_redirection = self.load(conf, self.tag, "FOLLOW_REDIRECTION")
        if _follow_redirection == "YES":
            self.follow_redirection = True
        else:
            self.follow_redirection = False
        _verify = self.load(conf, self.tag, "VERIFY_CERTIFICATE")
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
            thread = HTTPRequest(i, str(i), event, new_session, config.verify, config.follow_redirection, history_in_queue, history_out_queue)
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
def run_webdriver(url, timeout, follow_redirection=False, verify=False):
    if not follow_redirection:
        return url

    # Authentication session synchronization between requests and selenium problem. TODO:
    wd = webdriver.PhantomJS(executable_path="/usr/local/bin/phantomjs", service_args=["--ignore-ssl-errors="+str(not verify).lower(), "--ssl-protocol=any"])
    # wd = webdriver.Chrome(executable_path="/Users/hyili/Documents/Python/selenium/ChromeDriver/chromedriver")
    wd.set_page_load_timeout(timeout)
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
                if history[sub_url]["status_code"] in [400, 401, 403, 404, 500, 503, -3, -5]:
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

            if history[sub_url]["status_code"] in [400, 401, 403, 404, 500, 503, -3, -5]:
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
