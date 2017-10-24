#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


"""
Static Global variable
- total_links
    - this is used to record the total number of parsed links.
- total_output_links
    - this is used to record the total number of parsed links that are NOT in
    filter_code.
- history_out_queue
    - this is the message queue from worker thread to main thread to transfer history contains.
- history_in_queue
    - this is the message queue from main thread to worker thread to transfer history inputs.
"""
total_links = 0
total_output_links = 0
history_out_queue = None
history_in_queue = None

DEFAULT_CONFIG_TAG = "DEFAULT"
DEFAULT_CONFIG_PATH = "config/.requests.conf"
DEFAULT_DB_CONFIG_TAG = "MSSQL"
DEFAULT_DB_CONFIG_PATH = "config/.db.conf"
