#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import os
import csv
import datetime
from lxml import etree

import GlobalVars


"""
Output file generator using specified format
"""
def file_generator(history, logger, config, output_filename):
    # TODO: global variable recheck

    # Prevent directory issue
    output_filename = output_filename.replace("/", " ")
    if GlobalVars.total_output_links > 0:
        # TODO: logger reformat
        if "XML" in config.output_format:
            logger.warn("["+config.tag+"] filter_code: {"+str(config.filter_code)+"}, print_depth: {"+str(config.print_depth)+"} Generating "+output_filename+".xml ...")
        elif "CSV" in config.output_format:
            logger.warn("["+config.tag+"] filter_code: {"+str(config.filter_code)+"}, print_depth: {"+str(config.print_depth)+"} Generating "+output_filename+".csv ...")
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
                        if config.debug_mode:
                            print(e)
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
                        if config.debug_mode:
                            print(e)
                        continue
            tree = etree.ElementTree(time)
            with open(config.outputpath+"/"+output_filename+".xml", "ab", encoding="utf-8-sig") as xmlfile:
                tree.write(xmlfile, pretty_print=True)
                xmlfile.close()

    if "CSV" in config.output_format:
        file_exist = False
        if os.path.isfile(config.outputpath+"/"+output_filename+".csv"):
            file_exist = True

        fieldnames = ["日期時間", "從何而來", "連結網址", "連結名稱", "當前網址", "Certificate等級", "Certificate報告", "狀態碼", "第一層失連數", "負責人email", "負責人單位", "花費時間", "原因", "掃描層數", "共印出幾條網址", "共掃過幾條網址"]
        formatednames = [fieldnames[i-1] for i in config.type_setting]
        if config.sort == "URL":
            with open(config.outputpath+"/"+output_filename+".csv", "a", encoding="utf-8-sig") as csvfile:
                date_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y/%m/%d-%H:%M:%S")
                writer = csv.DictWriter(csvfile, fieldnames=formatednames)

                if not file_exist:
                    writer.writeheader()
                for log in history:
                    if history[log]["depth"] not in config.print_depth:
                        continue
                    if history[log]["status_code"] not in config.filter_code:
                        try:
                            # TODO: Group parent_url
                            if config.group_parent_url:
                                fielddata = [date_time, str(history[log]["parent_url"]), str(history[log]["link_url"]), str(history[log]["link_name"]), str(history[log]["current_url"]), str(history[log]["ssl_grade"]), str(history[log]["ssl_report_url"]), str(history[log]["status_code"]), str(history[log]["contained_broken_link"]), str(history[log]["admin_email"]), str(history[log]["admin_unit"]), str(history[log]["time_cost"]), str(history[log]["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                                row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                                writer.writerow(row)
                            else:
                                for parent_url in history[log]["parent_url"]:
                                    fielddata = [date_time, str(parent_url), str(history[log]["link_url"]), str(history[log]["link_name"]), str(history[log]["current_url"]), str(history[log]["ssl_grade"]), str(history[log]["ssl_report_url"]), str(history[log]["status_code"]), str(history[log]["contained_broken_link"]), str(history[log]["admin_email"]), str(history[log]["admin_unit"]), str(history[log]["time_cost"]), str(history[log]["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                                    row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                                    writer.writerow(row)
                        except Exception as e:
                            if config.debug_mode:
                                print(e)
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
                    if log["depth"] not in config.print_depth:
                        continue
                    if log["status_code"] not in config.filter_code:
                        try:
                            # TODO: Group parent_url
                            if config.group_parent_url:
                                fielddata = [date_time, str(log["parent_url"]), str(log["link_url"]), str(log["link_name"]), str(log["current_url"]), str(log["ssl_grade"]), str(log["ssl_report_url"]), str(log["status_code"]), str(log["contained_broken_link"]), str(log["admin_email"]), str(log["admin_unit"]), str(log["time_cost"]), str(log["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                                formateddata = [fielddata[i-1] for i in config.type_setting]
                                row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                                writer.writerow(row)
                            else:
                                for parent_url in log["parent_url"]:
                                    fielddata = [date_time, str(parent_url), str(log["link_url"]), str(log["link_name"]), str(log["current_url"]), str(log["ssl_grade"]), str(log["ssl_report_url"]), str(log["status_code"]), str(log["contained_broken_link"]), str(log["admin_email"]), str(log["admin_unit"]), str(log["time_cost"]), str(log["reason"]), str(config.depth), str(GlobalVars.total_output_links), str(GlobalVars.total_links)]
                                    formateddata = [fielddata[i-1] for i in config.type_setting]
                                    row = dict((formatednames[i], formateddata[i]) for i in range(0, len(formatednames)))
                                    writer.writerow(row)
                        except Exception as e:
                            if config.debug_mode:
                                print(e)
                            continue
                if config.depth != 0:
                    pass
                csvfile.close()

    if "JSON" in config.output_format:
        pass
    if "STDOUT" in config.output_format:
        print("\n"+str(history[config.target_url]["status_code"]))
