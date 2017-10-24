#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import configparser

import GlobalVars
import RequestException
from DB import MSSQLDB
from tool import Functions

"""
Config class
"""
class Config():
    def __init__(self):
        self.title = ""
        self.email = ""
        self.unit = ""

    # Wait for subclass implement
    def load():
        return None

    # Define what should load, and preprocess the config
    def load_config(self):
        # Specify the config that will load, and variable that will use
        _debug_mode = self.load("DEBUG_MODE")
        _auth = self.load("AUTH")
        _auth_url_pattern = self.load("AUTH_URL_PATTERN")
        _admin_email = self.load("ADMIN_EMAIL")
        _multithread = self.load("MULTITHREAD")
        _threshold = self.load("THRESHOLD", int)
        _print_depth = self.load("PRINT_DEPTH")
        _target_url = self.load("TARGET_URL")
        _current_url = _target_url
        _user = self.load("USER")
        _password = self.load("PASS")
        _header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2793.0 Safari/537.36"}
        _depth = self.load("DEPTH", int)
        _timeout = self.load("TIMEOUT", int)
        _domain_url = self.load("DOMAIN_URL", Functions.pattern_generator)
        _filter_code = self.load("FILTER")
        _ignore_code = self.load("IGNORE")
        _retry_code = self.load("RETRY")
        _broken_link = self.load("BROKEN_LINK")
        _max_retries = self.load("MAX_RETRIES", int)
        _output_format = self.load("FORMAT")
        _group_parent_url = self.load("GROUP_PARENT_URL")
        _sort = self.load("SORT")
        _follow_redirection = self.load("FOLLOW_REDIRECTION")
        _driver_location = self.load("DRIVER_LOCATION")
        _verify = self.load("VERIFY_CERTIFICATE")
        _ssllab_verify = self.load("SSLLAB_VERIFY_CERTIFICATE")
        _logpath = self.load("LOGPATH")
        _outputpath = self.load("OUTPUTPATH")
        _type_setting = self.load("TYPE_SETTING")

        # Preprocess the loaded config
        if _debug_mode == "YES":
            self.debug_mode = True
        else:
            self.debug_mode = False
        if _auth == "YES":
            self.auth = True
        else:
            self.auth = False
        self.auth_url_pattern = _auth_url_pattern
        self.admin_email = [str(i) for i in _admin_email.split(",")]
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
        if _group_parent_url == "YES":
            self.group_parent_url = True
        else:
            self.group_parent_url = False
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
        self.type_setting = [int(i) for i in _type_setting.split(",")]

class FileConfig(Config):
    def __init__(self, tag, config_path, default_config_path="config/.requests.conf.default"):
        self.tag = tag
        self.default_config_path = default_config_path
        self.config_path = config_path

        try:
            self.default_config = configparser.ConfigParser()
            self.default_config.read(self.default_config_path)
            self.default_config.sections()
        except Exception as e:
            raise RequestException.FileException("""Some error occurred when reading from default config.
                    Path: %s
                    Tag: %s
                    Reason: %s""" % (self.default_config_path, self.tag, str(e)))
        
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
                        Reason: %s""" % (self.config_path, self.tag, str(e)))

        if funct is None:
            return result
        else:
            return funct(result)

class MSSQLConfig(MSSQLDB, Config):
    def __init__(self, tag, config_path):
        # Call class MSSQLDB, no Config
        super().__init__(tag, config_path)
        self.config = None

    # Wait account & password (see it on server)
    def load(self, name, funct=None):
        # Fetch config data at first time
        if self.config == None:
            # TODO: how to get config
            sql = "SELECT *"
            self.cursor.execute(sql)
            self.config = self.cursor.fetchone()
        
        # Get the target config with name
        result = self.config[name]

        if funct is None:
            return result
        else:
            return funct(result)
