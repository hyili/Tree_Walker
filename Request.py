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

"""
Load user and password from file
"""
def load_conf(filename, tag):
    conf = ConfigParser.ConfigParser()
    conf.read(filename)
    conf.sections()
    try:
        auth = conf.get(tag, "AUTH")
        user = conf.get(tag, "USER")
        password = conf.get(tag, "PASS")
        depth = int(conf.get(tag, "DEPTH"))
        timeout = int(conf.get(tag, "TIMEOUT"))
        target_url = conf.get(tag, "TARGET_URL")
        target_url_pattern = conf.get(tag, "TARGET_URL_PATTERN")
        filter_pattern = conf.get(tag, "FILTER")
        output_format = conf.get(tag, "FORMAT")
        output_filename = conf.get(tag, "FILENAME")
        sort = conf.get(tag, "SORT")
        return {"AUTH": auth, "USER": user, "PASS": password, "DEPTH": depth, "TIMEOUT": timeout, "TARGET_URL": target_url, "TARGET_URL_PATTERN": target_url_pattern, "FILTER": filter_pattern, "FORMAT": output_format, "FILENAME": output_filename, "SORT": sort}
    except:
        print "No login profile found."
        quit()

"""
Navigate into the target website
"""
def navigate(session, target_url_pattern, current_url, linktexts, history, filter_code, timeout=5, depth=1):
    links = []
    total_linktexts = len(linktexts)
    counter = 1
    for linktext in linktexts:
        sys.stderr.write(str(counter)+"/"+str(total_linktexts)+"\r")
        counter += 1
        sub_url = factor_url(current_url, linktext[1])
        log = str((sub_url+" "+linktext[3]).encode("utf-8"))

        if sub_url in history:
            if current_url not in history[sub_url]["parent_url"]:
                history[sub_url]["parent_url"].append(current_url)
                history[sub_url]["link_name"].append(linktext[3])
            continue
        else:
            history[sub_url] = {"parent_url": [current_url], "link_name": [linktext[3]], "link_url": sub_url, "current_url": "", "status_code": -1, "time_cost": -1, "reason": ""}

        try:
            start_time = datetime.datetime.now()
            r = session.get(sub_url, timeout=timeout)
            r.encoding = "utf-8"
            end_time = datetime.datetime.now()

            history[sub_url]["time_cost"] = float((end_time-start_time).seconds) + float((end_time-start_time).microseconds) / 1000000.0
            history[sub_url]["status_code"] = r.status_code
            history[sub_url]["current_url"] = r.url
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
        except e:
            history[sub_url]["status_code"] = -7
            history[sub_url]["reason"] = e
            print log
            print "Unknown problem\n"
            continue

        print "Time costs: "+str(history[sub_url]["time_cost"])+"sec\n"

    if depth is 0:
        return

    for link in links:
        sub_url = link[0]
        sub_linktexts = find_linktexts(link[1])
        print "************************************************************"
        print sub_url
        print "************************************************************"
        navigate(session, target_url_pattern, sub_url, sub_linktexts, history, filter_code, timeout=timeout, depth=depth-1)

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
def authenticate(session, target_url, payload):
    try:
        r = session.post(target_url)
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
def file_generator(output_format, history, filter_code, sort, output_filename):
    if output_format == "XML":
        if sort == "URL":
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            for log in history:
                if history[log]["status_code"] not in filter_code:
                    locate = etree.SubElement(time, "locate")
                    locate.set("value", log)
                    parent_url = etree.SubElement(locate, "parent_url")
                    parent_url.set("value", str(history[log]["parent_url"]))
                    link_url = etree.SubElement(locate, "link_url")
                    link_url.set("value", history[log]["link_url"])
                    current_url = etree.SubElement(locate, "current_url")
                    current_url.set("value", history[log]["current_url"])
#                    link_name = etree.SubElement(locate, "link_name")
#                    link_name.set("value", history[log]["link_name"])
                    status_code = etree.SubElement(locate, "status_code")
                    status_code.set("value", str(history[log]["status_code"]))
                    time_cost = etree.SubElement(locate, "time_cost")
                    time_cost.set("value", str(history[log]["time_cost"]))
                    reason = etree.SubElement(locate, "reason")
                    reason.set("value", str(history[log]["reason"]))
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
                    parent_url = etree.SubElement(locate, "parent_url")
                    parent_url.set("value", str(log["parent_url"]))
                    link_url = etree.SubElement(locate, "link_url")
                    link_url.set("value", log["link_url"])
                    current_url = etree.SubElement(locate, "current_url")
                    current_url.set("value", log["current_url"])
#                    link_name = etree.SubElement(locate, "link_name")
#                    link_name.set("value", log["link_name"])
                    status_code = etree.SubElement(locate, "status_code")
                    status_code.set("value", str(log["status_code"]))
                    time_cost = etree.SubElement(locate, "time_cost")
                    time_cost.set("value", str(log["time_cost"]))
                    reason = etree.SubElement(locate, "reason")
                    reason.set("value", str(log["reason"]))
            tree = etree.ElementTree(time)
            tree.write(output_filename+".xml", pretty_print=True)

    elif output_format == "JSON":
        print "Not implement"
