#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import configparser

from tool import GlobalVars
from tool import RequestException
from tool import Functions

"""
Config class
"""
class Config():
    def __init__(self):
        self.title = ""
        self.email = ""
        self.unit = ""
        pass

    # Wait for subclass implement
    def load():
        return None

    # Define what should load, and preprocess the config
    def load_config(self):
        # Specify the config that will load, and variable that will use
        # TODO: change variable name to fit DB & config name
        _debug_mode = self.load("debug_mode")
        _auth = self.load("is_intra")
        _auth_url_pattern = self.load("sso_url")
        _admin_email = self.load("admin_email")
        _multithread = self.load("multithread")
        _threshold = self.load("threshold", int)
        _print_depth = self.load("report_level")
        _target_url = self.load("target_url")
        _current_url = _target_url
        _user = self.load("sso_id")
        _password = self.load("sso_passwd")
        _header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36"}
        _depth = self.load("search_level", int)
        _timeout = self.load("timeout", int)
        _domain_url = self.load("search_domain", Functions.pattern_generator)
        _filter_code = self.load("filter")
        _ignore_code = self.load("ignore")
        _retry_code = self.load("retry")
        _broken_link = self.load("search_status")
        _max_retries = self.load("max_retries", int)
        _output_format = self.load("output_format")
        _group_parent_url = self.load("group_parent_url")
        _sort = self.load("report_sort")
        _follow_redirection = self.load("follow_redirection")
        _driver_location = self.load("driver_location")
        _verify = self.load("verify_certificate")
        _ssllab_verify = self.load("ssllab_verify_certificate")
        _logpath = self.load("logpath")
        _outputpath = self.load("outputpath")
        _type_setting = self.load("type_setting")

        # Preprocess the loaded config
        if _debug_mode == "yes":
            self.debug_mode = True
        else:
            self.debug_mode = False
        if _auth == "yes":
            self.auth = True
        else:
            self.auth = False
        self.auth_url_pattern = _auth_url_pattern
        self.admin_email = [str(i) for i in _admin_email.split(",")]
        if _multithread == "yes":
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
        if _group_parent_url == "yes":
            self.group_parent_url = True
        else:
            self.group_parent_url = False
        self.sort = _sort
        if _follow_redirection == "yes":
            self.follow_redirection = True
        else:
            self.follow_redirection = False
        self.driver_location = _driver_location
        if _verify == "yes":
            self.verify = True
        else:
            self.verify = False
        if _ssllab_verify == "yes":
            self.ssllab_verify = True
        else:
            self.ssllab_verify = False
        self.logpath = _logpath
        self.outputpath = _outputpath
        self.type_setting = [int(i) for i in _type_setting.split(",")]

# read config from file, Default method
class FileConfig(Config):
    def __init__(self, tag, config_path):
        self.tag = tag
        self.config_path = config_path

        try:
            self.default_config = configparser.ConfigParser()
            self.default_config.read(GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH)
            self.default_config.sections()
        except Exception as e:
            raise RequestException.FileException("""Some error occurred when reading from default config.
                    Path: %s
                    Tag: %s
                    Reason: %s""" % (GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH, GlobalVars.DEFAULT_CONFIG_TAG, str(e)))
        
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
            self.config.sections()
        except Exception as e:
            raise RequestException.FileException("""Some error occurred when reading from config.
                    Path: %s
                    Tag: %s
                    Reason: %s""" % (self.config_path, self.tag, str(e)))

    # Function to load config, if option not exist in target tag, load from DEFAULT tag instead
    def load(self, option, funct=None):
        try:
            result = self.config.get(self.tag, option)
        except configparser.NoSectionError as e:
            raise RequestException.FileException("""Some error occurred when reading from config.
                    Path: %s
                    Tag: %s
                    Reason: %s""" % (self.config_path, self.tag, str(e)))
        except:
            try:
                result = self.default_config.get(GlobalVars.DEFAULT_CONFIG_TAG, option)
            except Exception as e:
                raise RequestException.FileException("""Some error occurred when reading from config.
                        Path: %s
                        Tag: %s
                        Reason: %s""" % (GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH, GlobalVars.DEFAULT_CONFIG_TAG, str(e)))

        if funct is None:
            return result
        else:
            return funct(result)
