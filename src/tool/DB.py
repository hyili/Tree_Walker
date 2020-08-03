#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import pymssql
import configparser

from tool import RequestException

class MSSQLDB():
    def __init__(self, tag, config_path):
        self._tag = tag
        self._config_path = config_path

        # Read server, username, password, database from config_path
        config = configparser.ConfigParser()
        config.read(config_path)
        config.sections()

        server = config.get(self._tag, "DB_SERV")
        port = config.get(self._tag, "DB_PORT")
        username = config.get(self._tag, "DB_USER")
        password = config.get(self._tag, "DB_PASS")
        database = config.get(self._tag, "DB_NAME")

        #print(server + username + password + database + port)
        # Connect to database
        # Parse parameter to cursor
        try:
            self.connection = pymssql.connect(server=server, user=username, password=password, database=database, port=port)
            self.cursor = self.connection.cursor(as_dict=True)
        except Exception as e:
            raise RequestException.DBException(("Some error occurred when connecting to database.\n" +
                    "Reason: %s") % (str(e)))

        # conversion
        pymssql.Binary = bytearray
    
    def Binary(self, binary_data):
        return pymssql.Binary(binary_data)

    def __del__(self):
        # Exception in __del__ will be ignored
        try:
            self.connection.close()
        except Exception as e:
            raise RequestException.DBException(("Some error occurred when closing the connection to database.\n" +
                    "Reason: %s") % (str(e)))

# You can implement new class here
class MYSQLDB():
    pass
