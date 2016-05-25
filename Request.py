#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
"""
Note: Need to set timeout when parsing the website
"""

import requests
import urllib.parse
import html.parser
import re
import configparser
import datetime
import sys
from lxml import etree
import csv
import threading
import queue

"""
Global variable
"""
total_links = 0
total_broken_links = 0
history_queue = queue.Queue(2000)
history_queue_lock = threading.Lock()

"""
Thread class
"""
class HTTPRequest(threading.Thread):
    def __init__(self, thread_id, thread_name, session, timeout, q):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.session = session
        self.timeout = timeout
        self.q = q
    def run(self):
        send_request(session=self.session, timeout=self.timeout, url=self.thread_name, q=self.q)

"""
Multithreaded HTTPRequest
"""
def send_request(session, timeout, url, q):
    current_url = ""
    status_code = -1
    time_cost = -1
    reason = ""
    r = None

    start_time = datetime.datetime.now()
    try:
        r = session.get(url, timeout=timeout)
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
    except:
        status_code = -7
        reason = "Unknown problem\n"

    end_time = datetime.datetime.now()
    time_cost = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0

    q.put({"sub_url": url, "current_url": current_url, "status_code": status_code, "time_cost": time_cost, "reason": reason, "response": r})

"""
Load user and password from file
"""
def load_conf(filename, tag):
    conf = configparser.ConfigParser()
    conf.read(filename)
    conf.sections()
    try:
        auth = conf.get(tag, "AUTH")
        multithread = conf.get(tag, "MULTITHREAD")
        threshold = int(conf.get(tag, "THRESHOLD"))
        target_url = conf.get(tag, "TARGET_URL")
        if auth == "YES":
            user = conf.get(tag, "USER")
            password = conf.get(tag, "PASS")
            payload = {"target": target_url, "USER": user, "PASSWORD": password}
        else:
            payload = {"target": target_url}
        depth = int(conf.get(tag, "DEPTH"))
        timeout = int(conf.get(tag, "TIMEOUT"))
        target_url_pattern = pattern_generator(conf.get(tag, "TARGET_URL_PATTERN"))
        filter_codes = conf.get(tag, "FILTER")
        filter_code = [int(i) for i in filter_codes.split(",")]
        output_formats = conf.get(tag, "FORMAT")
        output_format = [str(i) for i in output_formats.split(",")]
        sort = conf.get(tag, "SORT")
        return {"AUTH": auth, "MULTITHREAD": multithread, "THRESHOLD": threshold, "PAYLOAD": payload, "DEPTH": depth, "TIMEOUT": timeout, "TARGET_URL": target_url, "TARGET_URL_PATTERN": target_url_pattern, "FILTER": filter_code, "FORMAT": output_format, "SORT": sort}
    except:
        print("No login profile found.")
        quit()

"""
Navigate into the target website
"""
def navigate(session, multithread, threshold, target_url_pattern, current_url, linktexts, filter_code=[], history={}, timeout=5, depth=0):
    global total_links, total_broken_links, history_queue
    links = []
    total_linktexts = len(linktexts)
    total_links += total_linktexts
    depth -= 1
    counter = 1

    if multithread == "YES":
        thread_id = 0
        threads = []
        for linktext in linktexts:
            sub_url = factor_url(current_url, linktext[1])

            if sub_url in history:
                if current_url not in history[sub_url]["parent_url"]:
                    history[sub_url]["parent_url"].append(str(current_url))
                continue
            else:
                history[sub_url] = {"parent_url": [str(current_url)], "link_url": str(sub_url), "link_name": linktext[3], "current_url": "", "status_code": -1, "time_cost": -1, "reason": ""}

            thread = HTTPRequest(thread_id, sub_url, session, timeout, history_queue)
            thread.start()
            threads.append(thread)
            thread_id += 1

            if thread_id >= threshold:
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
                if bool(re.search(target_url_pattern, history[sub_url]["current_url"])):
                    if r is not None:
                        try:
                            links.append((r.url, r.content.decode(r.encoding)))
                        except:
                            links.append((r.url, r.text))
            elif history[sub_url]["status_code"] in filter_code:
                continue
            elif history[sub_url]["status_code"] == -6:
                del history[sub_url]
            else:
                total_broken_links += 1
                print(history[sub_url]["link_url"]+" "+history[sub_url]["link_name"])
                print(history[sub_url]["status_code"])

    else:
        for linktext in linktexts:
            sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
            counter += 1

            sub_url = factor_url(current_url, linktext[1])

            if sub_url in history:
                if current_url not in history[sub_url]["parent_url"]:
                    history[sub_url]["parent_url"].append(str(current_url))
                continue
            else:
                history[sub_url] = {"parent_url": [str(current_url)], "link_url": str(sub_url), "link_name": linktext[3], "current_url": "", "status_code": -1, "time_cost": -1, "reason": ""}

            send_request(session, timeout, sub_url, history_queue)
            result = history_queue.get()
            history[sub_url]["current_url"] = result["current_url"]
            history[sub_url]["status_code"] = result["status_code"]
            history[sub_url]["time_cost"] = result["time_cost"]
            history[sub_url]["reason"] = result["reason"]
            r = result["response"]

            if history[sub_url]["status_code"] == 200:
                if bool(re.search(target_url_pattern, history[sub_url]["current_url"])):
                    if r is not None:
                        try:
                            links.append((r.url, r.content.decode(r.encoding)))
                        except:
                            links.append((r.url, r.text))
            elif history[sub_url]["status_code"] in filter_code:
                continue
            elif history[sub_url]["status_code"] == -6:
                del history[sub_url]
            else:
                total_broken_links += 1
                print(history[sub_url]["link_url"]+" "+history[sub_url]["link_name"])
                print(history[sub_url]["status_code"])

    if depth <= 0:
        return history

    for link in links:
        sub_url = link[0]
        sub_linktexts = find_linktexts(source=link[1])
        print("************************************************************")
        print(sub_url)
        print("************************************************************")
        navigate(session=session, multithread=multithread, threshold=threshold, linktexts=sub_linktexts, filter_code=filter_code,  history=history, current_url=sub_url, target_url_pattern=target_url_pattern, timeout=timeout, depth=depth)

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
def authenticate(session, target_url, payload, auth):
    global total_links, total_broken_links
    history = {}
    history[target_url] = {"parent_url": [], "link_url": str(target_url), "link_name": "", "current_url": "", "status_code": -1, "time_cost": -1, "reason": ""}
    try:
        r = session.get(target_url)
        if auth == "YES":
            r = session.post(r.url, data=payload)
        total_links += 1
        history[target_url]["current_url"] = r.url
        history[target_url]["status_code"] = r.status_code
    except KeyboardInterrupt:
        print("Bye~ Bye~\n")
        quit()
    except requests.exceptions.HTTPError as e:
        history[target_url]["status_code"] = -2
        history[target_url]["reason"] = e
        quit()
    except requests.exceptions.Timeout as e:
        history[target_url]["status_code"] = -3
        history[target_url]["reason"] = e
        quit()
    except requests.exceptions.TooManyRedirects as e:
        history[target_url]["status_code"] = -4
        history[target_url]["reason"] = e
        quit()
    except requests.exceptions.ConnectionError as e:
        history[target_url]["status_code"] = -5
        history[target_url]["reason"] = e
        quit()
    except requests.exceptions.InvalidSchema as e:
        history[target_url]["status_code"] = -6
        history[target_url]["reason"] = e
        quit()
    except:
        history[target_url]["status_code"] = -7
        quit()

    if history[target_url]["status_code"] != 200:
        total_broken_links += 1

    try:
        ret_val = (r.content.decode(r.encoding), history)
    except:
        ret_val = (r.text, history)

    return ret_val

"""
Find all the link in the given source
"""
def find_linktexts(source):
    pattern = re.compile("<a([\s\S]*?)?href=\"([\s\S]*?)\"([\s\S]*)?>([\s\S]*?)?</a>")
    return re.findall(pattern, source)

"""
Output file generator using specified format
"""
def file_generator(history, filter_code=[], output_format=[], sort="STATUS_CODE", output_filename="DEFAULT"):
    global total_links, total_broken_links

    if total_broken_links == 0:
        return

    if "XML" in output_format:
        if sort == "URL":
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(total_links))
            total_broken_link = etree.SubElement(time, "total_broken_links")
            total_broken_link.set("value", str(total_broken_links))
            for log in history:
                if history[log]["status_code"] not in filter_code:
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
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(history[log]["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(history[log]["reason"]))
                    except:
                        print (history[log])
                        continue
            tree = etree.ElementTree(time)
            tree.write(output_filename+"-"+str(datetime.datetime.now())+".xml", pretty_print=True)
        elif sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(total_links))
            total_broken_link = etree.SubElement(time, "total_broken_links")
            total_broken_link.set("value", str(total_broken_links))
            for log in sort_by_status:
                if log["status_code"] not in filter_code:
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
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(log["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(log["reason"]))
                    except:
                        print (log)
                        continue
            tree = etree.ElementTree(time)
            tree.write(output_filename+"-"+str(datetime.datetime.now())+".xml", pretty_print=True)

    if "CSV" in output_format:
        if sort == "URL":
            with open(output_filename+"-"+str(datetime.datetime.now())+".csv", "w") as csvfile:
                fieldnames = ["parent_url", "link_url", "link_name", "current_url", "status_code", "time_cost", "reason", "total_links", "total_broken_links"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for log in history:
                    if history[log]["status_code"] not in filter_code:
                        try:
                            writer.writerow({"parent_url": str(history[log]["parent_url"]), "link_url": str(history[log]["link_url"]), "link_name": str(history[log]["link_name"]), "current_url": str(history[log]["current_url"]), "status_code": str(history[log]["status_code"]), "time_cost": str(history[log]["time_cost"]), "reason": str(history[log]["reason"])})
                        except:
                            print(history[log])
                            continue
                writer.writerow({"total_links": str(total_links), "total_broken_links": str(total_broken_links)})
        elif sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            with open(output_filename+"-"+str(datetime.datetime.now())+".csv", "w") as csvfile:
                fieldnames = ["parent_url", "link_url", "link_name", "current_url", "status_code", "time_cost", "reason", "total_links", "total_broken_links"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for log in sort_by_status:
                    if log["status_code"] not in filter_code:
                        try:
                            writer.writerow({"parent_url": str(log["parent_url"]), "link_url": str(log["link_url"]), "link_name": str(log["link_name"]), "current_url": str(log["current_url"]), "status_code": str(log["status_code"]), "time_cost": str(log["time_cost"]), "reason": str(log["reason"])})
                        except:
                            print(log)
                            continue
                writer.writerow({"total_links": str(total_links), "total_broken_links": str(total_broken_links)})

    if "JSON" in output_format:
        print("Not implement")

"""
transform the target_url to target_url_pattern in regular expression format
"""
def pattern_generator(target_url):
    target_url_pattern = target_url

    target_url_pattern = re.sub("\.", "\\.", target_url_pattern)
    target_url_pattern = re.sub("\:", "\\:", target_url_pattern)
    target_url_pattern = re.sub("\?", "\\?", target_url_pattern)
    target_url_pattern = re.sub("\*", "\\*", target_url_pattern)
    target_url_pattern = re.sub("\+", "\\+", target_url_pattern)
    target_url_pattern = re.sub("\^", "\\^", target_url_pattern)
    target_url_pattern = re.sub("\$", "\\$", target_url_pattern)
    target_url_pattern = re.sub("\~", "\\~", target_url_pattern)
    target_url_pattern = re.sub("\(", "\\(", target_url_pattern)
    target_url_pattern = re.sub("\)", "\\)", target_url_pattern)
    target_url_pattern = re.sub("\[", "\\[", target_url_pattern)
    target_url_pattern = re.sub("\]", "\\]", target_url_pattern)
    target_url_pattern = re.sub("\{", "\\{", target_url_pattern)
    target_url_pattern = re.sub("\}", "\\}", target_url_pattern)
    target_url_pattern = re.sub("\|", "\\|", target_url_pattern)
    target_url_pattern = re.sub("\&", "\\&", target_url_pattern)

    return target_url_pattern
