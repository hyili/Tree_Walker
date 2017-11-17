#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

from ITRI.ITRIDB import SQL2K5T

# TODO: database output handler
def db_handler(result, config):
    # This connection is for output use
    # it can be different from the connection in config variable.
    # That means input database and output database could be different.
    # But here, both use the same database
    sql2k5t = SQL2K5T(config.tag, config.config_path)

    # save back to tbl_mainInfo table
    sql2k5t.save_to_mainInfo(result, config)

    # save result to tbl_records table
    for record in result["data"]:
        sql2k5t.save_to_records(result, record, config)

    # commit changes
    sql2k5t.commit()
