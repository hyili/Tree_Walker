#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

from ITRI.ITRIDB import SQL2K5T

# TODO: database output handler
def db_handler(history, config):
    print("Do nothing now haha")

    # This connection is for output use
    # it can be different from the connection in config variable.
    # That means input database and output database could be different.
    # But here, both use the same database
    sql2k5t = SQL2K5T(config.tag, config.config_path)
