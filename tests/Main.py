#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import sys
import getpass
import signal
import logging
import datetime
import argparse
import traceback

import context
import ConfigLoader
import Output
from Request import Request
from tool import GlobalVars
from tool import Functions
from tool import History

from ITRI import ITRIConfigLoader
from ITRI import ITRIOutput

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
    auth_group = commandline_subparser.add_mutually_exclusive_group()
    auth_group.add_argument("--auth", default=None, dest="auth", action="store_true")
    auth_group.add_argument("--no-auth", default=None, dest="auth", action="store_false")
    return parser.parse_args()

"""
Parse function
"""
def parse_funct(filename, config, db_handler, enable_signal=True):
    start_time = datetime.datetime.now()
    history = {}
    result = {"start_time": start_time, "data": history, "exception": None}
    r = Request(config=config, decode="utf-8-sig")

    try:
        r.set_session()
        r.initialize()

        if enable_signal:
            signal.signal(signal.SIGINT, r.signal_handler)

        if config.depth >= 0:
            linktexts = []
            linktexts.append((config.target_url, config.target_name))
            history.update(r.navigate(linktexts=linktexts, history=history, config=config, decode="utf-8-sig"))
    except Exception as e:
        result["exception"] = e

    end_time = datetime.datetime.now()
    result["end_time"] = end_time
    Output.output_handler(result=result, config=config, output_filename=filename, db_handler=db_handler)
    r.close()

"""
Handler
- args for commandline input arguments, function call won't have this
"""
def handler(configargs=None, args=None):
    logging.basicConfig(filename="logs/error.report", filemode="a",
            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    # Enter from function call
    # Load configuration from self-defined DB configloader
    if args is None:
        # configargs comes from HTTP
        config = ITRIConfigLoader.QMCConfig(db_tag="ITSMDB", db_config_path=GlobalVars.DEFAULT_DB_CONFIG_PATH, file_tag="APISERVER", file_config_path=GlobalVars.DEFAULT_CONFIG_PATH, args=configargs)
        config.load_config()
        parse_funct(filename="APISERVER", config=config, db_handler=ITRIOutput.QMC_db_handler, enable_signal=False)

    # Enter from commandline
    elif args is not None:
        # Load configuration from config file
        # Example: ./Main.py config DEFAULT
        if args.subparser_name == "config":
            for tag in args.tags[0:]:
                config = ConfigLoader.FileConfig(tag=tag, config_path=GlobalVars.DEFAULT_CONFIG_PATH)
                config.load_config()
                parse_funct(filename=tag, config=config, db_handler=None)

        # Load configuration from commandline
        # Example: ./Main.py commandline --url https://hyili.idv.tw --depth 0
        elif args.subparser_name == "commandline":
            config = ConfigLoader.FileConfig(tag=args.tag, config_path=args.config)
            config.load_config()

            config.verify = args.verify if args.verify is not None else config.verify
            config.follow_redirection = args.redirect if args.redirect is not None else config.follow_redirection
            config.target_name = args.target_name
            config.target_url = Functions.factor_url(args.url, "")
            config.current_url = Functions.factor_url(args.url, "")
            config.domain_url = Functions.pattern_generator(args.url)
            config.auth = args.auth if args.auth is not None else config.auth
            if config.auth:
                print("User: ", end="", flush=True)
                config.payload["USER"] = sys.stdin.readline()
                config.payload["PASSWORD"] = getpass.getpass()
                config.payload["TARGET"] = config.target_url
            else:
                config.payload = {}

            if args.depth >= 0:
                config.depth = args.depth

            parse_funct(filename=args.filename, config=config, db_handler=None)

"""
Main function
"""
def main():
    argv = sys.argv
    args = arg_initialize(argv)
    try:
        handler(args=args)
    except Exception as e:
        print("Main(main())"+str(e))

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        print("")

if __name__ == "__main__":
    main()
    exit(0)
