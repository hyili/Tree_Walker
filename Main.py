#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import sys
import logging
import Request
import argparse

"""
Logger init
"""
def log_initialize(logname):
    logger = logging.getLogger("requests")
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(logname)
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

"""
Argument init
"""
def arg_initialize(argv):
    parser = argparse.ArgumentParser(description="Start to parse the website.")
    return parser

"""
Round function
"""
def round_funct(argv, logger):
    total_start_time = Request.datetime.datetime.now()
    for tag in argv[1:]:
        history = {}

        print("["+str(tag)+"]")
        conf = Request.load_config(filename=".requests.conf", tag=tag)

        session = Request.requests.Session()
        print("************************************************************")
        print(conf.target_url)
        print("************************************************************")
        (source, history) = Request.authenticate(session=session, config=conf)
        linktexts = Request.find_linktexts(source=source)
        if conf.depth > 0:
            history.update(Request.navigate(session=session, linktexts=linktexts, config=conf))
        Request.file_generator(history=history, config=conf, logger=logger, output_filename=tag)
        session.close()

    total_end_time = Request.datetime.datetime.now()
    print("Total time costs: "+str(float((total_end_time-total_start_time).seconds) + float((total_end_time-total_start_time).microseconds) / 1000000.0)+"sec\n")

"""
Main function
"""
if __name__ == "__main__":
    argv = sys.argv

    logger = log_initialize(".requests.log")
    parser = arg_initialize(argv)
    round_funct(argv, logger)
