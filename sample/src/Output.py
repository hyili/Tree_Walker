#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import csv
import datetime
from lxml import etree

from src import GlobalVars


"""
Output file generator using specified format
"""
def file_generator(history, logger, config, output_filename):
    # TODO: global variable recheck

    # Prevent directory issue
    output_filename = output_filename.replace("/", " ")
    if GlobalVars.total_output_links > 0:
        # TODO: logger reformat
        logger.warn("["+config.tag+"] filter_code: {"+str(config.filter_code)+"}, print_depth: {"+str(config.print_depth)+"} Generating "+output_filename+"...")
    if "XML" in config.output_format:
        if config.sort == "URL":
            time = etree.Element("time")
            time.set("value", str(datetime.datetime.now()))
            total_link = etree.SubElement(time, "total_links")
            total_link.set("value", str(GlobalVars.total_links))
            total_output_link = etree.SubElement(time, "total_output_links")
            total_output_link.set("value", str(GlobalVars.total_output_links))
            for log in history:
                if history[log]["depth"] not in config.print_depth:
                    continue
                if history[log]["status_code"] not in config.filter_code or history[log]["contained_broken_link"] != 0:
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
                        contained_broken_link = etree.SubElement(locate, "contained_broken_link")
                        contained_broken_link.set("value", str(history[log]["contained_broken_link"]))
                        admin_email = etree.SubElement(locate, "admin_email")
                        admin_email.set("value", str(history[log]["admin_email"]))
                        admin_unit = etree.SubElement(locate, "admin_unit")
                        admin_unit.set("value", str(history[log]["admin_unit"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(history[log]["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(history[log]["reason"]))
                    except Exception as e:
                        # print(e)
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
                if log["depth"] not in config.print_depth:
                    continue
                if log["status_code"] not in config.filter_code or log["contained_broken_link"] != 0:
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
                        contained_broken_link = etree.SubElement(locate, "contained_broken_link")
                        contained_broken_link.set("value", str(log["contained_broken_link"]))
                        admin_email = etree.SubElement(locate, "admin_email")
                        admin_email.set("value", str(log["admin_email"]))
                        admin_unit = etree.SubElement(locate, "admin_unit")
                        admin_unit.set("value", str(log["admin_unit"]))
                        time_cost = etree.SubElement(locate, "time_cost")
                        time_cost.set("value", str(log["time_cost"]))
                        reason = etree.SubElement(locate, "reason")
                        reason.set("value", str(log["reason"]))
                    except Exception as e:
                        # print(e)
                        continue
            tree = etree.ElementTree(time)
            with open(config.outputpath+"/"+output_filename+".xml", "ab", encoding="utf-8-sig") as xmlfile:
                tree.write(xmlfile, pretty_print=True)
                xmlfile.close()

    if "CSV" in config.output_format:
        file_exist = False
        if os.path.isfile(config.outputpath+"/"+output_filename+".csv"):
            file_exist = True

        if config.sort == "URL":
            with open(config.outputpath+"/"+output_filename+".csv", "a", encoding="utf-8-sig") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "Certificate等級", "Certificate報告", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "共印出幾條網址", "共掃過幾條網址"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exist:
                    writer.writeheader()
                for log in history:
                    if history[log]["depth"] not in config.print_depth:
                        continue
                    if history[log]["status_code"] not in config.filter_code or history[log]["contained_broken_link"] != 0:
                        try:
                            writer.writerow({"日期時間": date_time, "從何而來": str(history[log]["parent_url"]), "連結網址": str(history[log]["link_url"]), "連結名稱": str(history[log]["link_name"]), "當前網址": str(history[log]["current_url"]), "Certificate等級": str(history[log]["ssl_grade"]), "Certificate報告": str(history[log]["ssl_report_url"]), "狀態碼": str(history[log]["status_code"]), "第一層失連數": str(history[log]["contained_broken_link"]), "負責人email": str(history[log]["admin_email"]), "負責人單位": str(history[log]["admin_unit"]), "花費時間": str(history[log]["time_cost"]), "原因": str(history[log]["reason"])})
                        except Exception as e:
                            # print(e)
                            continue
                if config.depth != 0:
                    pass
                csvfile.close()
        elif config.sort == "STATUS_CODE":
            sort_by_status = sorted(iter(history.values()), key=lambda x : x["status_code"])
            with open(config.outputpath+"/"+output_filename+".csv", "a", encoding="utf-8-sig") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "Certificate等級", "Certificate報告", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "共印出幾條網址", "共掃過幾條網址"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exist:
                    writer.writeheader()
                for log in sort_by_status:
                    if log["depth"] not in config.print_depth:
                        continue
                    if log["status_code"] not in config.filter_code or log["contained_broken_link"] != 0:
                        try:
                            writer.writerow({"日期時間": date_time, "從何而來": str(log["parent_url"]), "連結網址": str(log["link_url"]), "連結名稱": str(log["link_name"]), "當前網址": str(log["current_url"]), "Certificate等級": str(log["ssl_grade"]), "Certificate報告": str(log["ssl_report_url"]), "狀態碼": str(log["status_code"]), "第一層失連數": str(log["contained_broken_link"]), "負責人email": str(log["admin_email"]), "負責人單位": str(log["admin_unit"]), "花費時間": str(log["time_cost"]), "原因": str(log["reason"])})
                        except Exception as e:
                            # print(e)
                            continue
                if config.depth != 0:
                    pass
                csvfile.close()

    if "JSON" in config.output_format:
        pass
    if "STDOUT" in config.output_format:
        print("\n"+str(history[config.target_url]["status_code"]))
