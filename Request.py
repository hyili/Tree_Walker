#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Note: Need to set timeout when parsing the website
"""

import requests
import urlparse
import HTMLParser
import re
import ConfigParser
import datetime
import sys
from lxml import etree
import csv

"""
Load user and password from file
"""
def load_conf(filename, tag):
    conf = ConfigParser.ConfigParser()
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
        target_url_pattern = conf.get(tag, "TARGET_URL_PATTERN")
        filter_pattern = conf.get(tag, "FILTER")
        filter_code = [int(i) for i in filter_pattern.split(",")]
        output_format = conf.get(tag, "FORMAT")
        output_filename = conf.get(tag, "FILENAME")
        if output_filename == "":
            output_filename = str(datetime.datetime.now())
        print output_filename
        sort = conf.get(tag, "SORT")
        return {"AUTH": auth, "PAYLOAD": payload, "DEPTH": depth, "TIMEOUT": timeout, "TARGET_URL": target_url, "TARGET_URL_PATTERN": target_url_pattern, "FILTER": filter_code, "FORMAT": output_format, "FILENAME": output_filename, "SORT": sort}
    except:
        print "No login profile found."
        quit()

"""
Navigate into the target website
"""
def navigate(session, target_url_pattern, current_url, linktexts, filter_code, history={}, timeout=5, depth=0):
    links = []
    total_linktexts = len(linktexts)
    depth -= 1
    counter = 1

    for linktext in linktexts:
        sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
        counter += 1
        sub_url = factor_url(current_url, linktext[1])
        log = str((sub_url+" "+linktext[3]).encode("utf-8"))

        if sub_url in history:
            if current_url not in history[sub_url]["parent_url"]:
                history[sub_url]["parent_url"].append(str(current_url.encode("utf-8")))
            continue
        else:
            history[sub_url] = {"parent_url": [str(current_url.encode("utf-8"))], "link_url": str(sub_url.encode("utf-8")), "current_url": "", "status_code": -1, "time_cost": -1, "reason": ""}

        try:
            start_time = datetime.datetime.now()
            r = session.get(sub_url, timeout=timeout)
            r.encoding = "utf-8"
            end_time = datetime.datetime.now()

            history[sub_url]["time_cost"] = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
            history[sub_url]["status_code"] = r.status_code
            history[sub_url]["current_url"] = str(r.url.encode("utf-8"))
            if r.status_code in filter_code:
                if bool(re.search(target_url_pattern, r.url)):
                    links.append((r.url, r.text))
                continue
            else:
                print log
                print r.status_code
        except KeyboardInterrupt:
            print "Bye~ Bye~\n"
            quit()
        except requests.exceptions.HTTPError as e:
            history[sub_url]["status_code"] = -2
            history[sub_url]["reason"] = e
            print log
            print str(e)+"\n"
            continue
        except requests.exceptions.Timeout as e:
            history[sub_url]["status_code"] = -3
            history[sub_url]["reason"] = e
            print log
            print str(e)+"\n"
            continue
        except requests.exceptions.TooManyRedirects as e:
            history[sub_url]["status_code"] = -4
            history[sub_url]["reason"] = e
            print log
            print str(e)+"\n"
            continue
        except requests.exceptions.ConnectionError as e:
            history[sub_url]["status_code"] = -5
            history[sub_url]["reason"] = e
            print log
            print str(e)+"\n"
            continue
        except requests.exceptions.InvalidSchema as e:
            history[sub_url]["status_code"] = -6
            history[sub_url]["reason"] = e
            # not record
            del history[sub_url]
            continue
        except:
            history[sub_url]["status_code"] = -7
            history[sub_url]["reason"] = "Unknown problem\n"
            print log
            print "Unknown problem\n"
            continue

        print "Time costs: "+str(history[sub_url]["time_cost"])+"sec\n"

    if depth <= 0:
        return history

    for link in links:
        sub_url = link[0]
        sub_linktexts = find_linktexts(source=link[1])
        print "************************************************************"
        print sub_url
        print "************************************************************"
        navigate(session=session, linktexts=sub_linktexts, history=history, current_url=sub_url, target_url_pattern=target_url_pattern, filter_code=filter_code, timeout=timeout, depth=depth)

    return history

"""
Reformat url
"""
def factor_url(current_url, sub_url):
    pattern = "^(javascript|tel):"
    if bool(re.search(pattern, sub_url)):
        return sub_url

    new_sub_url = HTMLParser.HTMLParser().unescape(sub_url)

    pattern = "^(ftp|http(s)?)://"
    if bool(re.search(pattern, new_sub_url)):
        return new_sub_url
    else:
        return urlparse.urljoin(current_url, new_sub_url).replace("../", "")

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
        print "Bye~ Bye~\n"
        quit()
    except requests.exceptions.HTTPError as e:
        print str(e)
        quit()
    except requests.exceptions.Timeout as e:
        print str(e)
        quit()
    except requests.exceptions.TooManyRedirects as e:
        print str(e)
        quit()
    except requests.exceptions.ConnectionError as e:
        print str(e)
        quit()
    except requests.exceptions.InvalidSchema as e:
        print str(e)
        quit()
    except:
        quit()

    return r.text

"""
Find all the link in the given source
"""
def find_linktexts(source):
    pattern = "<a(.*?)?href=\"(.*?)\"(.*)?>(.*?)?</a>"
    return re.findall(pattern, source)

"""
Output file generator using specified format
"""
def file_generator(history, output_format="XML", filter_code=[], sort="STATUS_CODE", output_filename="default"):
    if output_format == "XML":
        if sort == "URL":
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now().encode("utf-8")))
            for log in history:
                if history[log]["status_code"] not in filter_code:
                    locate = etree.SubElement(time, "locate")
                    locate.set("value", log)
                    try:
                        parent_url = etree.SubElement(locate, "parent_url")
                        parent_url.set("value", str(history[log]["parent_url"]))
                        link_url = etree.SubElement(locate, "link_url")
                        link_url.set("value", str(history[log]["link_url"]))
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
            tree.write(output_filename+".xml", pretty_print=True)
        elif sort == "STATUS_CODE":
            sort_by_status = sorted(history.itervalues(), key=lambda x : x["status_code"])
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
            tree.write(output_filename+".xml", pretty_print=True)

    elif output_format == "CSV":
        if sort == "URL":
            with open(output_filename+".csv", "w") as csvfile:
                fieldnames = ["parent_url", "link_url", "current_url", "status_code", "time_cost", "reason"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for log in history:
                    if history[log]["status_code"] not in filter_code:
                        try:
                            writer.writerow({"parent_url": str(history[log]["parent_url"]), "link_url": str(history[log]["link_url"]), "current_url": str(history[log]["current_url"]), "status_code": str(history[log]["status_code"]), "time_cost": str(history[log]["time_cost"]), "reason": str(history[log]["reason"])})
                        except:
                            print history[log]
                            continue
        elif sort == "STATUS_CODE":
            sort_by_status = sorted(history.itervalues(), key=lambda x : x["status_code"])
            with open(output_filename+".csv", "w") as csvfile:
                fieldnames = ["parent_url", "link_url", "current_url", "status_code", "time_cost", "reason"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for log in sort_by_status:
                    if log["status_code"] not in filter_code:
                        try:
                            writer.writerow({"parent_url": str(log["parent_url"]), "link_url": str(log["link_url"]), "current_url": str(log["current_url"]), "status_code": str(log["status_code"]), "time_cost": str(log["time_cost"]), "reason": str(log["reason"])})
                        except:
                            print log
                            continue


    elif output_format == "JSON":
        print "Not implement"
