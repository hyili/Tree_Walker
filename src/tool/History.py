#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

#
"""
history handler
"""
def history_handler(init=False, history=None, url="", link_url="", link_name="", status_code=-1, content_code=-1, time_cost=-1, context = "", reason="", start_time="", systep_id=""):
    if url == "" or history is None:
        print("History update failed.")
        return history

    if init:
        history[url] = {}
        history[url]["link_url"] = url
        history[url]["link_name"] = link_name
        history[url]["content_code"]=content_code
        history[url]["status_code"] = status_code
        history[url]["time_cost"] = time_cost
        history[url]["start_time"] = start_time
        history[url]["context"] = context
        #history[url]["auth"] = auth
        history[url]["reason"] = reason
        history[url]["systep_id"] = systep_id
    else:
        if url not in history:
            history_handler(init=True, history=history, url=url)
        if link_url != "":
            history[url]["link_url"] = url
        if link_name != "":
            history[url]["link_name"] = link_name
        if status_code != -1:
            history[url]["status_code"] = status_code
        if content_code != "":
            history[url]["content_code"] = content_code
        if time_cost != -1:
            history[url]["time_cost"] = time_cost
        if start_time != "":
            history[url]["start_time"] = start_time
        if context != "":
            history[url]["context"] = context
        #if context != "":
            #history[url]["auth"] = auth
        if reason != "":
            history[url]["reason"] = reason
        if systep_id != "":
            history[url]["systep_id"] = systep_id

    return history

