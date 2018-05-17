#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


"""
Static Global variable
- total_links
    - this is used to record the total number of parsed links.
- total_output_links
    - this is used to record the total number of parsed links that are NOT in filter_code.
"""
total_links = 0
total_output_links = 0

DEFAULT_CONFIG_TAG = "DEFAULT"
DEFAULT_CONFIG_PATH = "config/.requests.conf"
DEFAULT_DEFAULT_CONFIG_PATH = "config/.requests.conf.default"
DEFAULT_DB_CONFIG_TAG = "MSSQL"
DEFAULT_DB_CONFIG_PATH = "config/.db.conf"
DEFAULT_DEFAULT_DB_CONFIG_PATH = "config/.db.conf.default"
