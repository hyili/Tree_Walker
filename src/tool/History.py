#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


"""
history handler
"""
def history_handler(init=False, history=None, url="", parent_urls=None, link_url="", link_name="", current_url="", ssl_grade="?", ssl_report_url="", status_code=-1, start_time=None, end_time=None, time_cost=-1, query_time=-1, reason="", depth=-1, context_found=None):
    if url == "" or history is None:
        print("History update failed.")
        return history

    if init or url not in history:
        history[url] = {
                "parent_url": parent_urls,
                "link_url": link_url,
                "link_name": link_name,
                "current_url": current_url,
                "ssl_grade": ssl_grade,
                "ssl_report_url": ssl_report_url,
                "status_code": status_code,
                "start_time": start_time,
                "end_time": end_time,
                "time_cost": time_cost,
                "query_time": query_time,
                "reason": reason,
                "depth": depth,
                "context_found": context_found
        }
    else:
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
        if start_time is not None:
            history[url]["start_time"] = start_time
        if end_time is not None:
            history[url]["end_time"] = end_time
        if time_cost != -1:
            history[url]["time_cost"] = time_cost
        if query_time != -1:
            history[url]["query_time"] = query_time
        if reason != "":
            history[url]["reason"] = reason
        if depth != -1:
            history[url]["depth"] = depth
        if context_found is not None:
            history[url]["context_found"] = context_found

    return history

