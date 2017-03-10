#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


"""
history handler
"""
def history_handler(init=False, history=None, url="", parent_urls=None, link_url="", link_name="", current_url="", ssl_grade="?", ssl_report_url="", status_code=-1, contained_broken_link=0, admin_email="", admin_unit="", time_cost=-1, reason="", depth=-1):
    if url == "" or history is None:
        print("History update failed.")
        return history

    if init:
        history[url] = {}
        history[url]["parent_url"] = parent_urls
        history[url]["link_url"] = link_url
        history[url]["link_name"] = link_name
        history[url]["current_url"] = current_url
        history[url]["ssl_grade"] = ssl_grade
        history[url]["ssl_report_url"] = ssl_report_url
        history[url]["status_code"] = status_code
        history[url]["contained_broken_link"] = contained_broken_link
        history[url]["admin_email"] = admin_email
        history[url]["admin_unit"] = admin_unit
        history[url]["time_cost"] = time_cost
        history[url]["reason"] = reason
        history[url]["depth"] = depth
    else:
        if url not in history:
            history_handler(init=True, history=history, url=url)
        if parent_urls is not None:
            for parent_url in parent_urls:
                if parent_url not in history[url]["parent_url"]:
                    history[url]["parent_url"].append(parent_url)
        if link_url != "":
            history[url]["link_url"] = link_url
        if link_name != "":
            history[url]["link_name"] = link_name
        if current_url != "":
            history[url]["current_url"] = current_url
        if ssl_grade != "?":
            history[url]["ssl_grade"] = ssl_grade
        if ssl_report_url != "":
            history[url]["ssl_report_url"] = ssl_report_url
        if status_code != -1:
            history[url]["status_code"] = status_code
        if contained_broken_link != 0:
            history[url]["contained_broken_link"] = contained_broken_link
        if admin_email != "":
            history[url]["admin_email"] = admin_email
        if admin_unit != "":
            history[url]["admin_unit"] = admin_unit
        if time_cost != -1:
            history[url]["time_cost"] = time_cost
        if reason != "":
            history[url]["reason"] = reason
        if depth != -1:
            history[url]["depth"] = depth

    return history

