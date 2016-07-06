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
    subparsers = parser.add_subparsers(dest="subparser_name", help="2 subparsers provided.")
    subparsers.required = True
    config_subparser = subparsers.add_parser("config", help="Running specified config tag.")
    config_subparser.add_argument("tags", nargs="*", help="Specify tags in conf.")
    commandline_subparser = subparsers.add_parser("commandline", help="Running specified commandline option.")
    commandline_subparser.add_argument("--tag", default="DEFAULT", help="Template tag for commandline execution.", required=True)
    commandline_subparser.add_argument("--url", help="Specify target url.", required=True)
    commandline_subparser.add_argument("--depth", default=-1, type=int, help="Specify depth you want.")
    commandline_subparser.add_argument("--auth", dest="auth", action="store_true")
    commandline_subparser.add_argument("--no-auth", dest="auth", action="store_false")
    commandline_subparser.add_argument("--filename", help="Specify output filename.", required=True)
    return parser.parse_args()

"""
Parse function
"""
def parse_funct(tag, conf, logger):
    Request.initialize()
    session = Request.requests.Session()
    print("["+str(tag)+"]")
    print("************************************************************")
    print(conf.target_url)
    print("************************************************************")
    (source, history) = Request.authenticate(session=session, config=conf)
    linktexts = Request.find_linktexts(source=source)
    if conf.depth > 0:
        history.update(Request.navigate(session=session, linktexts=linktexts, config=conf))
    Request.file_generator(history=history, config=conf, logger=logger, output_filename=tag)
    session.close()

"""
Round function
"""
def round_funct(args, logger):
    if args.subparser_name == "config":
        for tag in args.tags[0:]:
            conf = Request.load_config(filename=".requests.conf", tag=tag)
            parse_funct(tag, conf, logger)
    elif args.subparser_name == "commandline":
        tag = args.filename
        conf = Request.load_config(filename=".requests.conf", tag=args.tag)

        conf.auth = args.auth
        conf.target_url = args.url
        conf.current_url = args.url
        conf.domain_url = Request.pattern_generator(args.url)

        if args.depth >= 0:
            conf.depth = args.depth

        parse_funct(tag, conf, logger)

"""
"""
def main():
    argv = sys.argv

    logger = log_initialize(".requests.log")
    args = arg_initialize(argv)

    total_start_time = Request.datetime.datetime.now()
    round_funct(args, logger)
    total_end_time = Request.datetime.datetime.now()
    print("Total time costs: "+str(float((total_end_time-total_start_time).seconds) + float((total_end_time-total_start_time).microseconds) / 1000000.0)+"sec\n")

"""
Main function
"""
if __name__ == "__main__":
    main()
