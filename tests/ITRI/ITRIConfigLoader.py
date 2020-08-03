#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import configparser

from tool import GlobalVars
from tool import RequestException
from ITRI.ITRIDB import SQL2K5T, ITSMDB
from ConfigLoader import Config, FileConfig

# Inherit SQL2K5T class to get ITRIDB connection & cursor
class SQL2K5TConfig(SQL2K5T, Config):
    # args comes from HTTP
    def __init__(self, tag, config_path, args):
        # Call class SQL2K5T with tag and config_path to connect to DB
        Config.__init__(self)
        SQL2K5T.__init__(self, tag, config_path)

        self.args = args
        self.mainInfo = None
        self.subInfo = None

        # temporarily read from default file
        # will read from FileConfig one day
        try:
            self.default_config = configparser.ConfigParser()
            self.default_config.read(GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH)
            self.default_config.sections()
        except Exception as e:
            raise RequestException.FileException(("Some error occurred when reading from default config.\n" +
                    "Path: %s\n" +
                    "Tag: %s\n" +
                    "Reason: %s") % (GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH, GlobalVars.DEFAULT_CONFIG_TAG, str(e)))

    # Load config from DB server
    def load(self, name, funct=None):
        # Fetch config data at first time
        if self.mainInfo is None and self.subInfo is None:
            if self.args["primid"]:
                self.get_tbl_mainInfo(self.args["primid"])
            # TODO: if subid is not found in db, how to do next?
            if self.args["subid"]:
                self.get_tbl_subInfo(self.args["subid"])
        
        # Get the target config with name
        try:
            if not self.args["subid"]:
                result = self.mainInfo[name]
            else:
                if name == "target_url":
                    result = self.subInfo["url"]
                elif name == "timeout":
                    result = self.subInfo["timewarn"]
                elif name == "redirection_timeout":
                    result = self.subInfo["redirection_timeout"]
                elif name == "is_intra":
                    result = self.subInfo["need_sso"]
                elif name == "context":
                    result = self.subInfo["context"]
                elif name == "follow_redirection":
                    result = self.subInfo["redirection"]
                elif name == "report_sort":
                    result = "STATUS_CODE"
                elif name == "steps":
                    result = self.subInfo["steps"]
                elif name == "args":
                    result = self.args
                else:
                    result = self.mainInfo[name]
        except:
            try:
                result = self.default_config.get(GlobalVars.DEFAULT_CONFIG_TAG, name)
            except Exception as e:
                raise RequestException.FileException(("Some error occurred when reading from config.\n" +
                        "Path: %s\n" +
                        "Tag: %s\n" +
                        "Reason: %s") % (GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH, GlobalVars.DEFAULT_CONFIG_TAG, str(e)))

        if name == "redirection_timeout":
            result = 5
        if result is None:
            raise RequestException.FileException(("Some error occurred when reading from config.\n"
                    "PrimID: %s\n" +
                    "SubID: %s\n" +
                    "Reason: name: %s is now %s") % (self.args["primid"], self.args["subid"], name, result))

        if funct is None:
            return result
        else:
            return funct(str(result))

# QMC configloader
class QMCConfig(Config):
    def __init__(self, db_tag, db_config_path, file_tag, file_config_path, args):
        super().__init__()
        self.f = FileConfig(file_tag, file_config_path)
        self.db = ITSMDB(db_tag, db_config_path)

        # args comes from HTTP
        self.args = args

    def load(self, name, funct=None):
        try:
            if name == "target_url":
                # TODO: For Demo
                #return "https://itriap9.itri.org.tw/isoc/index.aspx"

                # make a conversion from request args "sid" to url
                result = self.db.getUrl(self.args["sid"])
            elif name == "target_name":
                # TODO: For Demo
                #return "ISOC"

                # make a conversion from request args "sid" to name
                result = self.db.getName(self.args["sid"])
            elif name == "args":
                # records the HTTP request args
                result = self.args
            else:
                # Try to get from HTTP args
                result = self.args[name]
        except RequestException.DBException as e:
            raise e
        except Exception as e:
            result = self.f.load(name, funct)
            return result

        if funct is None:
            return result
        else:
            return funct(str(result))
