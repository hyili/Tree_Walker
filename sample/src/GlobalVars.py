#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-


"""
Global variable
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
global total_links
global total_output_links
global history_out_queue
global history_in_queue
