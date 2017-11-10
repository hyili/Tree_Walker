#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import configparser

from tool import GlobalVars
from tool import RequestException
from ITRI.ITRIDB import SQL2K5T
from ConfigLoader import Config

# Inherit SQL2K5T class to get ITRIDB connection & cursor
class SQL2K5TConfig(SQL2K5T, Config):
    def __init__(self, tag, config_path, args):
        # Call class SQL2K5T with tag and config_path to connect to DB
        Config.__init__(self)
        SQL2K5T.__init__(self, tag, config_path)

        self.args = args
        self.mainInfo = None
        self.subInfo = None

        # TODO: temporarily read from file
        try:
            self.default_config = configparser.ConfigParser()
            self.default_config.read(GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH)
            self.default_config.sections()
        except Exception as e:
            raise RequestException.FileException("""Some error occurred when reading from default config.
                    Path: %s
                    Tag: %s
                    Reason: %s""" % (GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH, GlobalVars.DEFAULT_CONFIG_TAG, str(e)))


    # Get mainInfo
    def get_tbl_mainInfo(self, primid):
        self.cursor.execute("SELECT * FROM tbl_mainInfo WHERE [id]='%s'" % (primid))
        self.mainInfo = self.cursor.fetchone()

    # Get subInfo
    def get_tbl_subInfo(self, subid):
        self.cursor.execute("SELECT * FROM tbl_subInfo WHERE [id]='%s'" %(subid))
        self.subInfo = self.cursor.fetchone()

    # Load config from DB server
    def load(self, name, funct=None):
        # Fetch config data at first time
        if self.mainInfo is None and self.subInfo is None:
            if self.args["primid"]:
                self.get_tbl_mainInfo(self.args["primid"])
            if self.args["subid"]:
                self.get_tbl_subInfo(self.args["subid"])
        
        # TODO: Get the target config with name
        try:
            result = self.mainInfo[name]
        # TODO: temporarily read from file
        except:
            try:
                result = self.default_config.get(GlobalVars.DEFAULT_CONFIG_TAG, name)
            except Exception as e:
                raise RequestException.FileException("""Some error occurred when reading from config.
                        Path: %s
                        Tag: %s
                        Reason: %s""" % (GlobalVars.DEFAULT_DEFAULT_CONFIG_PATH, GlobalVars.DEFAULT_CONFIG_TAG, str(e)))

        if funct is None:
            return result
        else:
            return funct(result)
