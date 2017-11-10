#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

from tool import RequestException
from tool.DB import MSSQLDB

class SQL2K5T(MSSQLDB):
    # TODO: define method when using db
    def __init__(self, tag, config_path):
        # Call class MSSQLDB.__init__() with tag and config_path to connect to DB
        # No calling Config's __init__
        super().__init__(tag, config_path)
