#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import pymssql
import configparser

import RequestException

class MSSQLDB():
    def __init__(self, tag, config_path):
        # Read server, username, password, database from config_path
        config = configparser.ConfigParser()
        config.read(config_path)
        config.sections()

        server = config.get(tag, "DB_SERV")
        username = config.get(tag, "DB_USER")
        password = config.get(tag, "DB_PASS")
        database = config.get(tag, "DB_NAME")

        # Connect to database
        try:
            self.connection = pymssql.connect(server=server, user=username, password=password, database=database)
            self.cursor = connection.cursor(as_dict=True)
        except Exception as e:
            raise RequestException.DBException("""Some error occurred when connecting to database. 
                    Reason: %s""" % (str(e)))
            
    def __del__(self):
        # Exception in __del__ will be ignored
        try:
            self.connection.close()
        except Exception as e:
            raise RequestException.DBException("""Some error occurred when closing the connection to database. 
                    Reason: %s""" % (str(e)))

