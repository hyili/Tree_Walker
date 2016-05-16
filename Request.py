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

"""
Global variable
"""
total_links = 0
total_broken_links = 0

"""
Load user and password from file
"""
def load_conf(filename, tag):
    conf = configparser.ConfigParser()
    conf.read(filename)
    conf.sections()
    try:
        auth = conf.get(tag, "AUTH")
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
        return {"AUTH": auth, "PAYLOAD": payload, "DEPTH": depth, "TIMEOUT": timeout, "TARGET_URL": target_url, "TARGET_URL_PATTERN": target_url_pattern, "FILTER": filter_code, "FORMAT": output_format, "SORT": sort}
    except :
        print("No login profile found.")
        quit()

"""
Navigate into the target website
"""
def navigate(session, target_url_pattern, current_url, linktexts, filter_code, history={}, timeout=5, depth=0):
    global total_links, total_broken_links
    links = []
    total_linktexts = len(linktexts)
    total_links += total_linktexts
    depth -= 1
    counter = 1

    for linktext in linktexts:
        sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
        counter += 1

        sub_url = factor_url(current_url, linktext[1])
        log = str((sub_url+" "+linktext[3]))

        if sub_url in history:
            if current_url not in history[sub_url]["parent_url"]:
                history[sub_url]["parent_url"].append(str(current_url))
            continue
        else:
            history[sub_url] = {"parent_url": [str(current_url)], "link_url": str(sub_url), "link_name": linktext[3], "current_url": "", "status_code": -1, "time_cost": -1, "reason": ""}

        try:
            start_time = datetime.datetime.now()
            r = session.get(sub_url, timeout=timeout)
            r.encoding = "utf-8"
            end_time = datetime.datetime.now()

            history[sub_url]["time_cost"] = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
            history[sub_url]["status_code"] = r.status_code
            history[sub_url]["current_url"] = str(r.url)
            if r.status_code in filter_code:
                if bool(re.search(target_url_pattern, r.url)):
                    links.append((r.url, r.content.decode(r.encoding)))
                continue
            else:
                total_broken_links += 1
                print(log)
                print(r.status_code)
        except KeyboardInterrupt:
            print("Bye~ Bye~\n")
            quit()
        except requests.exceptions.HTTPError as e:
            history[sub_url]["status_code"] = -2
            history[sub_url]["reason"] = e
            total_broken_links += 1
            print(log)
            print(str(e)+"\n")
            continue
        except requests.exceptions.Timeout as e:
            history[sub_url]["status_code"] = -3
            history[sub_url]["reason"] = e
            total_broken_links += 1
            print(log)
            print(str(e)+"\n")
            continue
        except requests.exceptions.TooManyRedirects as e:
            history[sub_url]["status_code"] = -4
            history[sub_url]["reason"] = e
            total_broken_links += 1
            print(log)
            print(str(e)+"\n")
            continue
        except requests.exceptions.ConnectionError as e:
            history[sub_url]["status_code"] = -5
            history[sub_url]["reason"] = e
            total_broken_links += 1
            print(log)
            print(str(e)+"\n")
            continue
        except requests.exceptions.InvalidSchema as e:
            history[sub_url]["status_code"] = -6
            history[sub_url]["reason"] = e
            total_broken_links += 1
            # do not record
            del history[sub_url]
            continue
        except:
            history[sub_url]["status_code"] = -7
            history[sub_url]["reason"] = "Unknown problem\n"
            total_broken_links += 1
            print(log)
            print("Unknown problem\n")
            continue

        print("Time costs: "+str(history[sub_url]["time_cost"])+"sec\n")

    if depth <= 0:
        return history

    for link in links:
        sub_url = link[0]
        sub_linktexts = find_linktexts(source=link[1])
        print("************************************************************")
        print(sub_url)
        print("************************************************************")
        navigate(session=session, linktexts=sub_linktexts, history=history, current_url=sub_url, target_url_pattern=target_url_pattern, filter_code=filter_code, timeout=timeout, depth=depth)

    return history

"""
Reformat url
"""
def factor_url(current_url, sub_url):
    pattern = "^(javascript|tel):"
    if bool(re.search(pattern, sub_url)):
        return sub_url

    new_sub_url = html.parser.HTMLParser().unescape(sub_url)

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
    try:
        r = session.post(target_url)
        if auth == "YES":
            r = session.post(r.url, data=payload)
    except KeyboardInterrupt:
        print("Bye~ Bye~\n")
        quit()
    except requests.exceptions.HTTPError as e:
        print(str(e))
        quit()
    except requests.exceptions.Timeout as e:
        print(str(e))
        quit()
    except requests.exceptions.TooManyRedirects as e:
        print(str(e))
        quit()
    except requests.exceptions.ConnectionError as e:
        print(str(e))
        quit()
    except requests.exceptions.InvalidSchema as e:
        print(str(e))
        quit()
    except:
        quit()

    return r.content.decode(r.encoding)

"""
Find all the link in the given source
"""
def find_linktexts(source):
    pattern = "<a(.*?)?href=\"(.*?)\"(.*)?>(.*?)?</a>"
    return re.findall(pattern, source)

"""
Output file generator using specified format
"""
def file_generator(history, output_format=[], filter_code=[], sort="STATUS_CODE", output_filename="DEFAULT"):
    global total_links, total_broken_links
    if "XML" in output_format:
        if sort == "URL":
            total_links = etree.Element("total_links")
            total_links.set("value", str(total_links))
            total_broken_links = etree.Element("total_broken_links")
            total_broken_links.set("value", str(total_broken_links))
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
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
                        continue
            tree = etree.ElementTree(time)
            tree.write(output_filename+"-"+str(datetime.datetime.now())+".xml", pretty_print=True)
        elif sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            total_links = etree.Element("total_links")
            total_links.set("value", str(total_links))
            total_broken_links = etree.Element("total_broken_links")
            total_broken_links.set("value", str(total_broken_links))
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
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
                        link_name.set("value", str(history[log]["link_name"]))
                        current_url = etree.SubElement(locate, "current_url")
                        current_url.set("value", str(log["current_url"]))
                        status_code = etree.SubElement(locate, "status_code")
                        status_code.set("value", str(log["status_code"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(log["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(log["reason"]))
                    except:
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
                writer.writerow({"total_links": total_links, "total_broken_links": total_broken_links})
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
                writer.writerow({"total_links": total_links, "total_broken_links": total_broken_links})

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
