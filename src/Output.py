#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import csv
import sys
import datetime
from lxml import etree

from tool import GlobalVars
from tool import RequestException

"""
XML Generator
"""
def xml_generator(history, config, output_filename):
    if config.sort == "URL":
        time = etree.Element("time")
        time.set("value", str(datetime.datetime.now()))
        total_link = etree.SubElement(time, "total_links")
        total_link.set("value", str(GlobalVars.total_links))
        total_output_link = etree.SubElement(time, "total_output_links")
        total_output_link.set("value", str(GlobalVars.total_output_links))
        for log in history:
            locate = etree.SubElement(time, "locate")
            locate.set("value", log)
            try:
                parent_url = etree.SubElement(locate, "parent_url")
                parent_url.set("value", str(history[log]["parent_url"]))
                link_url = etree.SubElement(locate, "link_url")
                link_url.set("value", str(history[log]["link_url"]))
                link_name = etree.SubElement(locate, "link_name")
                link_name.set("value", str(history[log]["link_name"]))
                current_url = etree.SubElement(locate, "current_url")
                current_url.set("value", str(history[log]["current_url"]))
                ssl_grade = etree.SubElement(locate, "ssl_grade")
                ssl_grade.set("value", str(history[log]["ssl_grade"]))
                ssl_report_url = etree.SubElement(locate, "ssl_report_url")
                ssl_report_url.set("value", str(history[log]["ssl_report_url"]))
                status_code = etree.SubElement(locate, "status_code")
                status_code.set("value", str(history[log]["status_code"]))
                time_cost = etree.SubElement(locate, "time_cost")
                time_cost.set("value", str(history[log]["time_cost"]))
                reason = etree.SubElement(locate, "reason")
                reason.set("value", str(history[log]["reason"]))
            except Exception as e:
                if config.debug_mode:
                    print("Output: "+str(e))
                continue
        tree = etree.ElementTree(time)
        with open(config.outputpath+"/"+output_filename+".xml", "ab", encoding="utf-8-sig") as xmlfile:
            tree.write(xmlfile, pretty_print=True)
            xmlfile.close()
    elif config.sort == "STATUS_CODE":
        sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
        time = etree.Element("time")
        time.set("value", str(datetime.datetime.now()))
        total_link = etree.SubElement(time, "total_links")
        total_link.set("value", str(GlobalVars.total_links))
        total_output_link = etree.SubElement(time, "total_output_links")
        total_output_link.set("value", str(GlobalVars.total_output_links))
        for log in sort_by_status:
            locate = etree.SubElement(time, "locate")
            locate.set("value", log["link_url"])
            try:
                parent_url = etree.SubElement(locate, "parent_url")
                parent_url.set("value", str(log["parent_url"]))
                link_url = etree.SubElement(locate, "link_url")
                link_url.set("value", str(log["link_url"]))
                link_name = etree.SubElement(locate, "link_name")
                link_name.set("value", str(log["link_name"]))
                current_url = etree.SubElement(locate, "current_url")
                current_url.set("value", str(log["current_url"]))
                ssl_grade = etree.SubElement(locate, "ssl_grade")
                ssl_grade.set("value", str(log["ssl_grade"]))
                ssl_report_url = etree.SubElement(locate, "ssl_report_url")
                ssl_report_url.set("value", str(log["ssl_report_url"]))
                status_code = etree.SubElement(locate, "status_code")
                status_code.set("value", str(log["status_code"]))
                time_cost = etree.SubElement(locate, "time_cost")
                time_cost.set("value", str(log["time_cost"]))
                reason = etree.SubElement(locate, "reason")
                reason.set("value", str(log["reason"]))
            except Exception as e:
                if config.debug_mode:
                    print("Output: "+str(e))
                continue
        tree = etree.ElementTree(time)
        with open(config.outputpath+"/"+output_filename+".xml", "ab", encoding="utf-8-sig") as xmlfile:
            tree.write(xmlfile, pretty_print=True)
            xmlfile.close()

"""
CSV Generator
"""
def csv_generator(history, config, output_filename):
    file_exist = False
    if os.path.isfile(config.outputpath+"/"+output_filename+".csv"):
        file_exist = True

    fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "Certificate等級", "Certificate報告", "狀態碼", "花費時間(秒)", "原因", "掃描層數", "共印出幾條網址", "共掃過幾條網址"]
    formatednames = [fieldnames[i-1] for i in config.type_setting]
    if config.sort == "URL":
        with open(config.outputpath+"/"+output_filename+".csv", "a", encoding="utf-8-sig") as csvfile:
            date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
            writer = csv.DictWriter(csvfile, fieldnames=formatednames)

            if not file_exist:
                writer.writeheader()
            for log in history:
                try:
                    # TODO: Group parent_url
                    if config.group_parent_url:
                        fielddata = [date_time, str(history[log]["parent_url"]), str(history[log]["link_url"]), str(history[log]["link_name"]), str(history[log]["current_url"]), str(history[log]["ssl_grade"]), str(history[log]["ssl_report_url"]), str(history[log]["status_code"]), str(history[log]["time_cost"]), str(history[log]["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                        row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                        writer.writerow(row)
                    else:
                        for parent_url in history[log]["parent_url"]:
                            fielddata = [date_time, str(parent_url), str(history[log]["link_url"]), str(history[log]["link_name"]), str(history[log]["current_url"]), str(history[log]["ssl_grade"]), str(history[log]["ssl_report_url"]), str(history[log]["status_code"]), str(history[log]["time_cost"]), str(history[log]["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                            row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                            writer.writerow(row)
                except Exception as e:
                    if config.debug_mode:
                        print("Output: "+str(e))
                    continue
            if config.depth != 0:
                pass
            csvfile.close()
    elif config.sort == "STATUS_CODE":
        sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
        with open(config.outputpath+"/"+output_filename+".csv", "a", encoding="utf-8-sig") as csvfile:
            date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
            writer = csv.DictWriter(csvfile, fieldnames=formatednames)

            if not file_exist:
                writer.writeheader()
            for log in sort_by_status:
                try:
                    # TODO: Group parent_url
                    if config.group_parent_url:
                        fielddata = [date_time, str(log["parent_url"]), str(log["link_url"]), str(log["link_name"]), str(log["current_url"]), str(log["ssl_grade"]), str(log["ssl_report_url"]), str(log["status_code"]), str(log["time_cost"]), str(log["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                        formateddata = [fielddata[i-1] for i in config.type_setting]
                        row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                        writer.writerow(row)
                    else:
                        if len(log["parent_url"]) == 0:
                            fielddata = [date_time, "", str(log["link_url"]), str(log["link_name"]), str(log["current_url"]), str(log["ssl_grade"]), str(log["ssl_report_url"]), str(log["status_code"]), str(log["time_cost"]), str(log["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                            formateddata = [fielddata[i-1] for i in config.type_setting]
                            row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                            writer.writerow(row)
                                
                        for parent_url in log["parent_url"]:
                            fielddata = [date_time, str(parent_url), str(log["link_url"]), str(log["link_name"]), str(log["current_url"]), str(log["ssl_grade"]), str(log["ssl_report_url"]), str(log["status_code"]), str(log["time_cost"]), str(log["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                            formateddata = [fielddata[i-1] for i in config.type_setting]
                            row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                            writer.writerow(row)
                except Exception as e:
                    if config.debug_mode:
                        print("Output: "+str(e))
                    continue
            if config.depth != 0:
                pass
            csvfile.close()

"""
JSON Generator
"""
def json_generator():
    pass

"""
STDOUT Generator
"""
def stdout_generator(result, config):
    print("\n"+str(result["data"][config.target_url]["status_code"]))
    sys.stdout.buffer.write(str(result).encode("utf-8-sig"))
    #print(str(result)) # Need to add PYHTONIOENCODING=utf-8-sig

"""
Output handler using specified format
"""
def output_handler(result, config, output_filename, db_handler):
    # Prevent directory issue
    output_filename = output_filename.replace("/", " ")

    # If generate output file is needed
    if GlobalVars.total_output_links > 0:
        if "XML" in config.output_format:
            # Out-of-date
            xml_generator(result["data"], config, output_filename)

        if "CSV" in config.output_format:
            csv_generator(result["data"], config, output_filename)

        if "JSON" in config.output_format:
            # Not implement yet
            json_generator()

    if "STDOUT" in config.output_format:
        stdout_generator(result, config)

    if "DB" in config.output_format:
        # TODO: Not implement yet
        try:
            db_handler(result, config)
        except Exception as e:
            raise RequestException.UnknownException("""The function called has unknown exception.
                    Reason: %s""" % (str(e)))

