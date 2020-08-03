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
        try:
            self.cursor.execute("""UPDATE [tbl_mainInfo] SET [check_sub] = %s, [receive_time] = %s,
                    [search_time] = %s, [found_url_no] = %d, [searched_url_no] = %d WHERE [id] = %s""",
                    (check_sub, str(config.args["datetime"])[0:-3], str(result["start_time"])[0:-3],
                    GlobalVars.total_output_links, GlobalVars.total_links, str(config.args["primid"])))
        except Exception as e:
            raise RequestException.DBException(("Some error ocurred when update data into DB.\n" +
                    "Reason: UPDATE [tbl_mainInfo] SET [check_sub] = %s, [receive_time] = %s,\n" +
                    "[search_time] = %s, [found_url_no] = %d, [searched_url_no] = %d WHERE [id] = %s\n" +
                    "Exception Details: %s")%
                    (check_sub, str(config.args["datetime"])[0:-3], str(result["start_time"])[0:-3],
                    GlobalVars.total_output_links, GlobalVars.total_links, config.args["primid"], str(e)))

    def save_to_records(self, result, record, config):
        history = result["data"]
        context_found = "T" if history[record]["context_found"] else "F"
        sso_check = "T" if config.sso_check else "F"

        # mainInfo_id, from_url, checked_name, checked_url, current_url, reason, found_level, check_time, spend_time, rtn_status, context_found, sso_check
        for url in history[record]["parent_url"]:
            try:
                self.cursor.execute("""INSERT INTO [tbl_records] ([mainInfo_id], [from_url], [checked_name],
                        [checked_url], [current_url], [reason], [found_level], [check_time], [spend_time],
                        [query_time], [rtn_status], [context_found], [sso_check], [steps]) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (str(config.args["primid"]), str(url), str(history[record]["link_name"]),
                        str(history[record]["link_url"]), str(history[record]["current_url"]),
                        str(history[record]["reason"]), history[record]["depth"],
                        str(history[record]["start_time"])[0:-3], history[record]["time_cost"], 
                        str(history[record]["query_time"]), str(history[record]["status_code"]),
                        context_found, sso_check, str(config.steps)))
            except Exception as e:
                raise RequestException.DBException(("Some error ocurred when insert data into DB.\n" +
                        "Reason: INSERT INTO [tbl_records] ([mainInfo_id], [from_url], [checked_name],\n" +
                        "[checked_url], [current_url], [reason], [found_level], [check_time], [spend_time],\n" +
                        "[query_time], [rtn_status], [context_found], [sso_check], [steps])\n" +
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n" +
                        "Exception Details: %s")%
                        (str(config.args["primid"]), str(url), str(history[record]["link_name"]),
                        str(history[record]["link_url"]), str(history[record]["current_url"]), 
                        str(history[record]["reason"]), history[record]["depth"],
                        str(history[record]["start_time"])[0:-3], str(history[record]["time_cost"]), 
                        str(history[record]["query_time"]), str(history[record]["status_code"]),
                        context_found, sso_check, str(config.steps), str(e)))

    def commit(self):
        self.connection.commit()


class ITRIDPO(MSSQLDB):
    # define method when using db
    def __init__(self, tag, config_path):
        # Call class MSSQLDB.__init__() with tag and config_path to connect to DB
        # No calling Config's __init__
        super().__init__(tag, config_path)

    # Database table field [Sid],[URL],[Time],[ResponseTime],[Status],[failImg]
    def insert(self, result, index, config):
        record = result["data"][index]
        sid = config.args["sid"]

        if config.save_screenshot and record["status_code"] != 200:
            self.cursor.execute("""INSERT INTO [ISOC_Transaction] ([Sid], [URL], [Time], [ResponseTime], [Status], [failImg])
                    VALUES (%s, %s, %s, %s, %s, %s)""", 
                    (str(sid), str(record["current_url"]), str(record["start_time"])[0:-3], str(record["query_time"]),
                    str(record["status_code"]), self.Binary(record["screenshot"])))
        else:
            self.cursor.execute("""INSERT INTO [ISOC_Transaction] ([Sid], [URL], [Time], [ResponseTime], [Status], [failImg])
                    VALUES (%s, %s, %s, %s, %s, %s)""", 
                    (str(sid), str(record["current_url"]), str(record["start_time"])[0:-3], str(record["query_time"]),
                    str(record["status_code"]), self.Binary(b"")))

    # Insert the error message to the database
    def insertException(self, result, config):
        sid = config.args["sid"]

        self.cursor.execute("""INSERT INTO [ISOC_Transaction] ([Sid], [URL], [Time], [ResponseTime], [Status], [failImg])
                VALUES (%s, %s, %s, %s, %s, %s)""", 
                (str(sid), str(result["exception"]), str(result["start_time"])[0:-3], str(-1),
                str(-7), self.Binary(b"")))

    def commit(self):
        self.connection.commit()

class ITSMDB(MSSQLDB):
    # define method when using db
    def __init__(self, tag, config_path):
        # Call class MSSQLDB.__init__() with tag and config_path to connect to DB
        # No calling Config's __init__
        super().__init__(tag, config_path)

        self.record = None

    # Get url from sid (service id)
    def getUrl(self, sid):
        if self.record is None or self.record["A-20150511-00002"] != sid:
            self.cursor.execute("SELECT [NAME],[A-20150617-00010],[A-20150511-00002],[Status] FROM [vwCI_TYPE_Service] WHERE [A-20150511-00002] = %s AND [Status] = 0", (sid))
            self.record = self.cursor.fetchone()
            if self.record is None:
                raise RequestException.DBException(("Some error ocurred when reading data from DB.\n" + 
                        "Reason: SELECT [NAME],[A-20150617-00010],[A-20150511-00002],[Status] FROM [vwCI_TYPE_Service] WHERE [A-20150511-00002] = %s AND [Status] = 0\n" +
                        "Exception Details: %s")%
                        (str(sid), "No such record."))

        if self.record["A-20150617-00010"] is None:
            raise RequestException.DBException(("Some error ocurred when reading data from DB.\n" + 
                    "Reason: SELECT [NAME],[A-20150617-00010],[A-20150511-00002],[Status] FROM [vwCI_TYPE_Service] WHERE [A-20150511-00002] = %s AND [Status] = 0\n" +
                    "Exception Details: %s")%
                    (str(sid), "Empty value retrieved."))

        return self.record["A-20150617-00010"]

    def getName(self, sid):
        if self.record is None or self.record["A-20150511-00002"] != sid:
            self.cursor.execute("SELECT [NAME],[A-20150617-00010],[A-20150511-00002],[Status] FROM [vwCI_TYPE_Service] WHERE [A-20150511-00002] = %s AND [Status] = 0", (sid))
            self.record = self.cursor.fetchone()
            if self.record is None:
                raise RequestException.DBException(("Some error ocurred when reading data from DB.\n" + 
                        "Reason: SELECT [NAME],[A-20150617-00010],[A-20150511-00002],[Status] FROM [vwCI_TYPE_Service] WHERE [A-20150511-00002] = %s AND [Status] = 0\n" +
                        "Exception Details: %s")%
                        (str(sid), "No such record."))

        return self.record["NAME"]

    def commit(self):
        self.connection.commit()
