#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

from tool import GlobalVars
from tool import RequestException
from tool.DB import MSSQLDB

class SQL2K5T(MSSQLDB):
    # TODO: define method when using db
    def __init__(self, tag, config_path):
        # Call class MSSQLDB.__init__() with tag and config_path to connect to DB
        # No calling Config's __init__
        super().__init__(tag, config_path)
    
    # Get mainInfo
    def get_tbl_mainInfo(self, primid):
        self.cursor.execute("SELECT * FROM tbl_mainInfo WHERE [id] = %s", (primid))
        self.mainInfo = self.cursor.fetchone()

    # Get subInfo
    def get_tbl_subInfo(self, subid):
        self.cursor.execute("SELECT * FROM tbl_subInfo WHERE [id] = %s",(subid))
        self.subInfo = self.cursor.fetchone()

    def save_to_mainInfo(self, result, config):
        check_sub = "Y" if config.args["subid"] else "N"

        # search_time, found_url_no, searched_url_no, report_size
        # TODO: check_sub is strange
        self.cursor.execute("""UPDATE [tbl_mainInfo] SET [check_sub] = %s, [receive_time] = %s, [search_time] = %s, [found_url_no] = %d,
                [searched_url_no] = %d WHERE [id] = %s""",
                (check_sub, str(config.args["datetime"])[0:-3], str(result["start_time"])[0:-3], GlobalVars.total_output_links, 
                GlobalVars.total_links, config.args["primid"]))

    def save_to_records(self, result, record, config):
        history = result["data"]
        context_found = "T" if history[record]["context_found"] else "F"
        sso_check = "T" if config.sso_check else "F"

        # mainInfo_id, from_url, checked_name, checked_url, current_url, reason, found_level, check_time, spend_time, rtn_status, context_found, sso_check
        for url in history[record]["parent_url"]:
            self.cursor.execute("""INSERT INTO [tbl_records] ([mainInfo_id], [from_url], [checked_name], [checked_url], [current_url], [reason],
                    [found_level], [check_time], [spend_time], [rtn_status], [context_found], [sso_check]) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (config.args["primid"], url, history[record]["link_name"], history[record]["link_url"], history[record]["current_url"], 
                    str(history[record]["reason"]), history[record]["depth"], str(history[record]["start_time"])[0:-3], history[record]["time_cost"], 
                    history[record]["status_code"], context_found, sso_check))

    def commit(self):
        self.connection.commit()
