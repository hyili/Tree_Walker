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
    parser.add_argument("tags", nargs="*", default=["DEFAULT"], help="Specify the tags in the conf.")
    parser.add_argument("--url", default="https://itriweb.itri.org.tw", help="Specify the target url. (Not implement)")
    parser.add_argument("--depth", default=2, type=int, help="Specify the depth you want. (Default is 2, not implement)")
    return parser.parse_args()

"""
Round function
"""
def round_funct(argv, logger):
    total_start_time = Request.datetime.datetime.now()
    for tag in argv[0:]:
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
"""
def main():
    argv = sys.argv

    logger = log_initialize(".requests.log")
    args = arg_initialize(argv)
    round_funct(args.tags, logger)

"""
Main function
"""
if __name__ == "__main__":
    main()
