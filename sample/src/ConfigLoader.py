#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import configparser

from src.tool import Functions

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

    def load(self, config, tag, option, funct=None):
        try:
            result = config.get(tag, option)
        except configparser.NoSectionError as e:
            # print(e)
            quit()
        except:
            try:
                result = config.get("DEFAULT", option)
            except Exception as e:
                # print(e)
                quit()

        if funct is None:
            return result
        else:
            return funct(result)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.filename)
        config.sections()

        _auth = self.load(config, self.tag, "AUTH")
        _multithread = self.load(config, self.tag, "MULTITHREAD")
        _threshold = self.load(config, self.tag, "THRESHOLD", int)
        _print_depth = self.load(config, self.tag, "PRINT_DEPTH")
        _target_url = self.load(config, self.tag, "TARGET_URL")
        _current_url = _target_url
        _user = self.load(config, self.tag, "USER")
        _password = self.load(config, self.tag, "PASS")
        _header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36"}
        _depth = self.load(config, self.tag, "DEPTH", int)
        _timeout = self.load(config, self.tag, "TIMEOUT", int)
        _domain_url = self.load(config, self.tag, "DOMAIN_URL", Functions.pattern_generator)
        _filter_code = self.load(config, self.tag, "FILTER")
        _ignore_code = self.load(config, self.tag, "IGNORE")
        _retry_code = self.load(config, self.tag, "RETRY")
        _broken_link = self.load(config, self.tag, "BROKEN_LINK")
        _max_retries = self.load(config, self.tag, "MAX_RETRIES", int)
        _output_format = self.load(config, self.tag, "FORMAT")
        _sort = self.load(config, self.tag, "SORT")
        _follow_redirection = self.load(config, self.tag, "FOLLOW_REDIRECTION")
        _driver_location = self.load(config, self.tag, "DRIVER_LOCATION")
        _verify = self.load(config, self.tag, "VERIFY_CERTIFICATE")
        _ssllab_verify = self.load(config, self.tag, "SSLLAB_VERIFY_CERTIFICATE")
        _logpath = self.load(config, self.tag, "LOGPATH")
        _outputpath = self.load(config, self.tag, "OUTPUTPATH")

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
        self.target_url = Functions.factor_url(_target_url, "")
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
        self.ignore_code = [int(i) for i in _ignore_code.split(",")]
        self.retry_code = [int(i) for i in _retry_code.split(",")]
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
        if _ssllab_verify == "YES":
            self.ssllab_verify = True
        else:
            self.ssllab_verify = False
        self.logpath = _logpath
        self.outputpath = _outputpath
