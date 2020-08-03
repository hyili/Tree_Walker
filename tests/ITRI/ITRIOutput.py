#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

from ITRI.ITRIDB import SQL2K5T, ITRIDPO
from tool import GlobalVars

# SQL2K5T database output handler
def SQL2K5T_db_handler(result, config):
    # This connection is for output use
    # it can be different from the connection in config variable.
    # That means input database and output database could be different.
    # But here, ***both use the same database***
    sql2k5t = SQL2K5T("SQL2K5T", GlobalVars.DEFAULT_DB_CONFIG_PATH)

    # save back to tbl_mainInfo table
    sql2k5t.save_to_mainInfo(result, config)

    # save result to tbl_records table
    for record in result["data"]:
        sql2k5t.save_to_records(result, record, config)

    # commit changes
    #sql2k5t.commit()

#  QMC db output handler
def QMC_db_handler(result, config):
    # Both ITRIDPO and ITSMDB use the same db config file
    itridpo = ITRIDPO("ITRIDPO", GlobalVars.DEFAULT_DB_CONFIG_PATH)

    if result["exception"] is not None:
        itridpo.insertException(result, config)
    else:
        # insert records one by one
        for index in result["data"]:
            itridpo.insert(result, index, config)

    # TODO: commit changes
    #itridpo.commit()
