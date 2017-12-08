#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import sys
import signal
import logging
import datetime
import argparse

import context
import ConfigLoader
import Request
import Output
from tool import GlobalVars
from tool import Functions

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
    commandline_subparser.add_argument("--tag", default="COMMANDLINE", help="Template tag for commandline execution.")
    commandline_subparser.add_argument("--url", help="Specify target url.", required=True)
    commandline_subparser.add_argument("--depth", default=-1, type=int, help="Specify depth you want.")
    cert_group = commandline_subparser.add_mutually_exclusive_group()
    cert_group.add_argument("--verify-cert", default=None, dest="verify", action="store_true")
    cert_group.add_argument("--no-verify-cert", default=None, dest="verify", action="store_false")
    redirect_group = commandline_subparser.add_mutually_exclusive_group()
    redirect_group.add_argument("--redirect", default=None, dest="redirect", action="store_true")
    redirect_group.add_argument("--no-redirect", default=None, dest="redirect", action="store_false")
    commandline_subparser.add_argument("--filename", default="commandline", help="Specify output filename.")
    commandline_subparser.add_argument("--config", default="config/.requests.conf", help="Specify the config file.")
    commandline_subparser.add_argument("--target_name", default="", help="Specify parsing link name.")
    commandline_subparser.add_argument("--description", default="", help="Specify the request description.")
    return parser.parse_args()

"""
Close function
"""
def close():
    Request.close()

"""
Parse function
"""
def parse_funct(filename, config, db_handler):
    start_time = datetime.datetime.now()
    history = {}
    result = {"start_time": start_time, "data": history}
    Request.initialize(config=config, decode="utf-8-sig")
    logging.basicConfig(filename="logs/error.report", filemode="a",
            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    if config.depth >= 0:
        linktexts = []
        linktexts.append((config.target_url, config.target_name))
        history.update(Request.navigate(linktexts=linktexts, history=history, config=config, decode="utf-8-sig"))
    Output.output_handler(result=result, config=config, output_filename=filename, db_handler=db_handler)
    close()

"""
Handler
- args for commandline input arguments, function call won't have this
"""
def handler(configloader, configargs=None, args=None, db_handler=None):
    # Signal handler
    try:
        signal.signal(signal.SIGINT, Request.signal_handler)
    # Do nothing in main thread
    except:
        pass

    # Enter from function call
    # Load configuration from self-defined DB configloader
    if args is None:
        # configargs for APIServer input index
        config = configloader(tag=GlobalVars.DEFAULT_DB_CONFIG_TAG, config_path=GlobalVars.DEFAULT_DB_CONFIG_PATH, args=configargs)
        config.load_config()
        parse_funct("APIServer-Tests", config, db_handler)

    # Enter from commandline
    elif args is not None:
        # Load configuration from config file
        # Example: ./Main.py config DEFAULT
        if args.subparser_name == "config":
            for tag in args.tags[0:]:
                config = configloader(tag=tag, config_path=GlobalVars.DEFAULT_CONFIG_PATH)
                config.load_config()
                parse_funct(tag, config, db_handler)

        # Load configuration from commandline
        # Example: ./Main.py commandline --url https://hyili.idv.tw --depth 0
        elif args.subparser_name == "commandline":
            config = configloader(tag=args.tag, config_path=args.config)
            config.load_config()

            config.verify = args.verify if args.verify is not None else config.verify
            config.follow_redirection = args.redirect if args.redirect is not None else config.follow_redirection
            config.target_name = args.target_name
            config.target_url = Functions.factor_url(args.url, "")
            config.current_url = Functions.factor_url(args.url, "")
            config.domain_url = Functions.pattern_generator(args.url)

            if args.depth >= 0:
                config.depth = args.depth

            parse_funct(args.filename, config, db_handler)

"""
Main function
"""
def main():
    argv = sys.argv
    args = arg_initialize(argv)
    handler(configloader=ConfigLoader.FileConfig, args=args)

if __name__ == "__main__":
    main()
    exit(0)
