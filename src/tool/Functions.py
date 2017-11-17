#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

# ***** #
# This file is for functions that may be used in multiple places
# ***** #

import re
import requests
import html.parser
import urllib.parse
from bs4 import BeautifulSoup

"""
Encoding detection
"""
def detect_encoding(r):
    content1 = None
    content2 = None
    header = None

    try:
        contentsoup = BeautifulSoup(r.content.decode("utf-8-sig", "ignore"), "lxml")
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
    except Exception as e:
        return None

"""
transform the target_url to domain_url in regular expression format
"""
def pattern_generator(target_url):
    domain_url = target_url

    domain_url = re.sub("http(s)?\://", "", domain_url)
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
Find the specified context
"""
def find_context(source, context):
    if source is None:
        return False

    pattern = re.compile(context)
    if bool(re.search(pattern, source)):
        return True
    else:
        return False
