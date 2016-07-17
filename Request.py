#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
"""
Note: Need to set timeout when parsing the website
"""

import requests
import urllib.parse
import html.parser
import os
import re
import configparser
import datetime
import sys
from lxml import etree
import csv
import threading
import queue
from selenium import webdriver

"""
Global variable
- total_links
    - this is used to record the total number of parsed links.
- total_output_links
    - this is used to record the total number of parsed links that are NOT in
    filter_code.
- history_queue
    - this is the message queue between thread to transfer history contains.
"""
total_links = 0
total_output_links = 0
history_queue = queue.Queue(2000)

"""
Thread class
"""
class HTTPRequest(threading.Thread):
    def __init__(self, thread_id, thread_name, session, header, timeout, q):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.session = session
        self.header = header
        self.timeout = timeout
        self.q = q
    def run(self):
        send_request(session=self.session, header=self.header, timeout=self.timeout, url=self.thread_name, q=self.q)

"""
Config class
"""
class Config():
    def __init__(self, auth, multithread, threshold, title, email, unit, print_depth, target_url, current_url, domain_url, header, payload, depth, timeout, filter_code, output_format, sort):
        self.auth = auth
        self.multithread = multithread
        self.threshold = threshold
        self.title = title
        self.email = email
        self.unit = unit
        self.print_depth = print_depth
        self.target_url = target_url
        self.current_url = current_url
        self.domain_url = domain_url
        self.header = header
        self.payload = payload
        self.depth = depth
        self.timeout = timeout
        self.filter_code = filter_code
        self.output_format = output_format
        self.sort = sort

"""
Initialize variable
"""
def initialize():
    global total_links, total_output_links, history_queue

    total_links = 0
    total_output_links = 0
    history_queue = queue.Queue(2000)

"""
Multithreaded HTTPRequest
"""
def send_request(session, header, timeout, url, q):
    current_url = ""
    status_code = -1
    time_cost = -1
    reason = ""
    r = None

    start_time = datetime.datetime.now()
    try:
        r = session.get(url, timeout=timeout, headers=header)
        status_code = r.status_code
        current_url = str(r.url)
    except KeyboardInterrupt:
        print("Bye~ Bye~\n")
        quit()
    except requests.exceptions.HTTPError as e:
        status_code = -2
        reason = e
    except requests.exceptions.Timeout as e:
        status_code = -3
        reason = e
    except requests.exceptions.TooManyRedirects as e:
        status_code = -4
        reason = e
    except requests.exceptions.ConnectionError as e:
        status_code = -5
        reason = e
    except requests.exceptions.InvalidSchema as e:
        status_code = -6
        reason = e
        # do not record
    except Exception as e:
        status_code = -7
        reason = e

    end_time = datetime.datetime.now()
    time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0

    q.put({"sub_url": url, "current_url": current_url, "status_code": status_code, "time_cost": time_cost, "reason": reason, "response": r})

"""
Selenium Web Driver
- just use selenium for web url after redirecting
"""
def execute_script(url):
    wd = webdriver.Firefox()
    wd.get(url)
    return wd.current_url

"""
Load option from given tag
"""
def load(conf, tag, option, funct=None):
    try:
        result = conf.get(tag, option)
    except configparser.NoSectionError as e:
        print(e)
        quit()
    except:
        try:
            result = conf.get("DEFAULT", option)
        except:
            #print("Default option "+option+" broken")
            quit()

    if funct is None:
        return result
    else:
        return funct(result)

"""
Load user and password from file
"""
def load_config(filename, tag):
    conf = configparser.ConfigParser()
    conf.read(filename)
    conf.sections()

    _auth = load(conf, tag, "AUTH")
    if _auth == "YES":
        auth = True
    else:
        auth = False
    _multithread = load(conf, tag, "MULTITHREAD")
    if _multithread == "YES":
        multithread = True
    else:
        multithread = False
    threshold = load(conf, tag, "THRESHOLD", int)
    title = ""
    email = ""
    unit = ""
    print_depths = load(conf, tag, "PRINT_DEPTH")
    print_depth = [int(i) for i in print_depths.split(",")]
    target_url = load(conf, tag, "TARGET_URL")
    current_url = target_url
    if auth:
        user = load(conf, tag, "USER")
        password = load(conf, tag, "PASS")
        header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Charset": "utf-8;q=0.7,*;q=0.3", "Connection": "keep-alive"}
        payload = {"USER": user, "PASSWORD": password}
    else:
        header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Charset": "utf-8;q=0.7,*;q=0.3", "Connection": "keep-alive"}
        payload = {}
    depth = load(conf, tag, "DEPTH", int)
    timeout = load(conf, tag, "TIMEOUT", int)
    domain_url = load(conf, tag, "DOMAIN_URL", pattern_generator)
    filter_codes = load(conf, tag, "FILTER")
    filter_code = [int(i) for i in filter_codes.split(",")]
    output_formats = load(conf, tag, "FORMAT")
    output_format = [str(i) for i in output_formats.split(",")]
    sort = load(conf, tag, "SORT")

    return Config(auth, multithread, threshold, title, email, unit, print_depth, target_url, current_url, domain_url, header, payload, depth, timeout, filter_code, output_format, sort)

"""
Navigate into the target website
"""
def navigate(session, linktexts, config, depth=1, history={}, decode=None):
    global total_links, total_output_links, history_queue

    links = []
    total_linktexts = len(linktexts)
    total_links += total_linktexts
    counter = 1

    if config.multithread:
        thread_id = 0
        threads = []
        for linktext in linktexts:
            sub_url = factor_url(config.current_url, linktext[1])

            if sub_url in history:
                if config.current_url not in history[sub_url]["parent_url"]:
                    history[sub_url]["parent_url"].append(str(config.current_url))
                continue
            else:
                history[sub_url] = {"parent_url": [str(config.current_url)], "link_url": str(sub_url), "link_name": linktext[3], "current_url": "", "status_code": -1, "contained_broken_link": 0, "admin_email": "", "admin_unit": "", "time_cost": -1, "reason": "", "depth": depth}

            thread = HTTPRequest(thread_id, sub_url, session, config.header, config.timeout, history_queue)
            thread.start()
            threads.append(thread)
            thread_id += 1

            if thread_id >= config.threshold:
                for thread in threads:
                    sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
                    counter += 1
                    thread.join()
                    threads.remove(thread)
                thread_id = 0

        for thread in threads:
            sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
            counter += 1
            thread.join()
            threads.remove(thread)

        while not history_queue.empty():
            result = history_queue.get()
            sub_url = result["sub_url"]
            history[sub_url]["current_url"] = result["current_url"]
            history[sub_url]["status_code"] = result["status_code"]
            history[sub_url]["time_cost"] = result["time_cost"]
            history[sub_url]["reason"] = result["reason"]
            r = result["response"]

            if history[sub_url]["status_code"] == 200:
                if bool(re.search(config.domain_url, history[sub_url]["current_url"])):
                    if r is not None:
                        try:
                            if decode is None:
                                links.append((r.url, r.content.decode(r.encoding)))
                            else:
                                links.append((r.url, r.content.decode(decode)))
                        except:
                            links.append((r.url, r.text))

            if history[sub_url]["status_code"] in [400, 401, 403, 404, 500, 503, -3, -5]:
                history[config.current_url]["contained_broken_link"] += 1

            if history[sub_url]["status_code"] not in config.filter_code and history[sub_url]["status_code"] != -6:
                total_output_links += 1

            if history[sub_url]["status_code"] == -6:
                del history[sub_url]

    else:
        for linktext in linktexts:
            sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
            counter += 1

            sub_url = factor_url(config.current_url, linktext[1])

            if sub_url in history:
                if config.current_url not in history[sub_url]["parent_url"]:
                    history[sub_url]["parent_url"].append(str(config.current_url))
                continue
            else:
                history[sub_url] = {"parent_url": [str(config.current_url)], "link_url": str(sub_url), "link_name": linktext[3], "current_url": "", "status_code": -1, "contained_broken_link": 0, "admin_email": "", "admin_unit": "", "time_cost": -1, "reason": "", "depth": depth}

            send_request(session, config.header, config.timeout, sub_url, history_queue)
            result = history_queue.get()
            history[sub_url]["current_url"] = result["current_url"]
            history[sub_url]["status_code"] = result["status_code"]
            history[sub_url]["time_cost"] = result["time_cost"]
            history[sub_url]["reason"] = result["reason"]
            r = result["response"]

            if history[sub_url]["status_code"] == 200:
                if bool(re.search(config.domain_url, history[sub_url]["current_url"])):
                    if r is not None:
                        try:
                            if decode is None:
                                links.append((r.url, r.content.decode(r.encoding)))
                            else:
                                links.append((r.url, r.content.decode(decode)))
                        except:
                            links.append((r.url, r.text))

            if history[sub_url]["status_code"] in [400, 401, 403, 404, 500, 503, -3, -5]:
                history[config.current_url]["contained_broken_link"] += 1

            if history[sub_url]["status_code"] not in config.filter_code and history[sub_url]["status_code"] != -6:
                total_output_links += 1

            if history[sub_url]["status_code"] == -6:
                del history[sub_url]

    if config.depth == depth:
        return history

    for link in links:
        sub_url = link[0]
        sub_linktexts = find_linktexts(source=link[1])
        config.current_url = sub_url
        history.update(navigate(session=session, linktexts=sub_linktexts, config=config, depth=depth+1, history=history))

    return history

"""
Reformat url
"""
def factor_url(current_url, sub_url):
    new_sub_url = re.sub("\\\\", "/", sub_url)

    pattern = "^(javascript|tel):"
    if bool(re.search(pattern, new_sub_url)):
        return new_sub_url

    new_sub_url = html.parser.HTMLParser().unescape(new_sub_url)

    pattern = "^(ftp|http(s)?)://"
    if bool(re.search(pattern, new_sub_url)):
        return new_sub_url
    else:
        return urllib.parse.urljoin(current_url, new_sub_url).replace("../", "")

"""
Will be forwarded to another authentication page
Then, login with payload information
"""
def authenticate(session, config, depth=0, decode=None):
    global total_links, total_output_links
    history = {}
    history[config.target_url] = {"parent_url": [], "link_url": str(config.target_url), "link_name": "", "current_url": "", "status_code": -1, "contained_broken_link": 0, "admin_email": "", "admin_unit": "", "time_cost": -1, "reason": "", "depth": depth}

    start_time = datetime.datetime.now()
    try:
        total_links += 1
        r = session.get(config.target_url, headers=config.header)
        if config.auth:
            r = session.post(r.url, headers=config.header, data=config.payload)
        history[config.target_url]["current_url"] = r.url
        history[config.target_url]["status_code"] = r.status_code
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
    except KeyboardInterrupt:
        print("Bye~ Bye~\n")
        quit()
    except requests.exceptions.HTTPError as e:
        history[config.target_url]["status_code"] = -2
        if history[config.target_url]["status_code"] not in config.filter_code:
            total_output_links += 1
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
        history[config.target_url]["reason"] = e
        return ("", history)
    except requests.exceptions.Timeout as e:
        history[config.target_url]["status_code"] = -3
        if history[config.target_url]["status_code"] not in config.filter_code:
            total_output_links += 1
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
        history[config.target_url]["reason"] = e
        return ("", history)
    except requests.exceptions.TooManyRedirects as e:
        history[config.target_url]["status_code"] = -4
        if history[config.target_url]["status_code"] not in config.filter_code:
            total_output_links += 1
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
        history[config.target_url]["reason"] = e
        return ("", history)
    except requests.exceptions.ConnectionError as e:
        history[config.target_url]["status_code"] = -5
        if history[config.target_url]["status_code"] not in config.filter_code:
            total_output_links += 1
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
        history[config.target_url]["reason"] = e
        return ("", history)
    except requests.exceptions.InvalidSchema as e:
        history[config.target_url]["status_code"] = -6
        if history[config.target_url]["status_code"] not in config.filter_code:
            total_output_links += 1
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
        history[config.target_url]["reason"] = e
        return ("", history)
    except Exception as e:
        history[config.target_url]["status_code"] = -7
        if history[config.target_url]["status_code"] not in config.filter_code:
            total_output_links += 1
        history[config.target_url]["link_name"] = config.title
        history[config.target_url]["admin_email"] = config.email
        history[config.target_url]["admin_unit"] = config.unit
        history[config.target_url]["reason"] = e
        return ("", history)

    end_time = datetime.datetime.now()
    time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
    history[config.target_url]["time_cost"] = time_cost

    if history[config.target_url]["status_code"] not in config.filter_code:
        total_output_links += 1

    try:
        if decode is None:
            ret_val = (r.content.decode(r.encoding), history)
        else:
            ret_val = (r.content.decode(decode), history)
    except:
        ret_val = (r.text, history)

    return ret_val

"""
Find all the link in the given source
"""
def find_linktexts(source):
    pattern = re.compile("<a([\s\S]*?)?href=\"([\s\S]*?)?\"([\s\S]*?)?>([\s\S]*?)?</a>")
    return re.findall(pattern, source)

"""
Output file generator using specified format
"""
def file_generator(history, logger, config, output_filename):
    global total_links, total_output_links

    logger.warn("["+output_filename+"] "+str(config.filter_code)+" "+str(total_output_links)+"/"+str(total_links)+" Genrating output files...")
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
                if history[log]["status_code"] not in config.filter_code:
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
            with open(output_filename+".xml", "ab") as xmlfile:
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
                if log["status_code"] not in config.filter_code:
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
            with open(output_filename+".xml", "ab") as xmlfile:
                tree.write(xmlfile, pretty_print=True)
                xmlfile.close()

    if "CSV" in config.output_format:
        file_exist = False
        if os.path.isfile(output_filename+".csv"):
            file_exist = True

        if config.sort == "URL":
            with open(output_filename+".csv", "a") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                #fieldnames = ["datetime", "parent_url", "link_url", "link_name", "current_url", "status_code", "contained_broken_link", "admin_email", "admin_unit", "time_cost", "reason", "total_output_links", "total_links"]
                fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "共印出幾條網址", "共掃過幾條網址"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exist:
                    writer.writeheader()
                for log in history:
                    if history[log]["depth"] not in config.print_depth:
                        continue
                    if history[log]["status_code"] not in config.filter_code:
                        try:
                            #writer.writerow({"datetime": date_time, "parent_url": str(history[log]["parent_url"]), "link_url": str(history[log]["link_url"]), "link_name": str(history[log]["link_name"]), "current_url": str(history[log]["current_url"]), "status_code": str(history[log]["status_code"]), "contained_broken_link": str(history[log]["contained_broken_link"]), "admin_email": str(history[log]["admin_email"]), "admin_unit": str(history[log]["admin_unit"]), "time_cost": str(history[log]["time_cost"]), "reason": str(history[log]["reason"])})
                            writer.writerow({"日期時間": date_time, "從何而來": str(history[log]["parent_url"]), "連結網址": str(history[log]["link_url"]), "連結名稱": str(history[log]["link_name"]), "當前網址": str(history[log]["current_url"]), "狀態碼": str(history[log]["status_code"]), "第一層失連數": str(history[log]["contained_broken_link"]), "負責人email": str(history[log]["admin_email"]), "負責人單位": str(history[log]["admin_unit"]), "花費時間": str(history[log]["time_cost"]), "原因": str(history[log]["reason"])})
                        except Exception as e:
                            print(e)
                            continue
                #writer.writerow({"datetime": date_time, "total_output_links": str(total_output_links), "total_links": str(total_links)})
                if config.depth != 0:
                    #writer.writerow({"日期時間": date_time, "共印出幾條網址": str(total_output_links), "共掃過幾條網址": str(total_links)})
                    pass
                csvfile.close()
        elif config.sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            with open(output_filename+".csv", "a") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                #fieldnames = ["datetime", "parent_url", "link_url", "link_name", "current_url", "status_code", "contained_broken_link", "admin_email", "admin_unit", "time_cost", "reason", "total_links", "total_output_links"]
                fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "共印出幾條網址", "共掃過幾條網址"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exist:
                    writer.writeheader()
                for log in sort_by_status:
                    if log["depth"] not in config.print_depth:
                        continue
                    if log["status_code"] not in config.filter_code:
                        try:
                            #writer.writerow({"datetime": date_time, "parent_url": str(log["parent_url"]), "link_url": str(log["link_url"]), "link_name": str(log["link_name"]), "current_url": str(log["current_url"]), "status_code": str(log["status_code"]), "contained_broken_link": str(log["contained_broken_link"]), "admin_email": str(log["admin_email"]), "admin_unit": str(log["admin_unit"]), "time_cost": str(log["time_cost"]), "reason": str(log["reason"])})
                            writer.writerow({"日期時間": date_time, "從何而來": str(log["parent_url"]), "連結網址": str(log["link_url"]), "連結名稱": str(log["link_name"]), "當前網址": str(log["current_url"]), "狀態碼": str(log["status_code"]), "第一層失連數": str(log["contained_broken_link"]), "負責人email": str(log["admin_email"]), "負責人單位": str(log["admin_unit"]), "花費時間": str(log["time_cost"]), "原因": str(log["reason"])})
                        except Exception as e:
                            print(e)
                            continue
                #writer.writerow({"datetime": date_time, "total_output_links": str(total_output_links), "total_links": str(total_links)})
                if config.depth != 0:
                    #writer.writerow({"日期時間": date_time, "共印出幾條網址": str(total_output_links), "共掃過幾條網址": str(total_links)})
                    pass
                csvfile.close()

    if "JSON" in config.output_format:
        #print("Not implement")
        pass
    if "STDOUT" in config.output_format:
        print(history[config.target_url]["status_code"])

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
