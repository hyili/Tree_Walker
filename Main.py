#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import Request
import logging
import argparse

"""
Logger init
"""
def log_initialize(logname):
    directory = "logs/"
    logger = logging.getLogger("main")
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(directory+logname)
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
    commandline_subparser.add_argument("--tag", default="COMMANDLINE", help="Template tag for commandline execution.", required=True)
    commandline_subparser.add_argument("--url", help="Specify target url.", required=True)
    commandline_subparser.add_argument("--depth", default=-1, type=int, help="Specify depth you want.")
    auth_group = commandline_subparser.add_mutually_exclusive_group()
    auth_group.add_argument("--auth", default=None, dest="auth", action="store_true")
    auth_group.add_argument("--no-auth", default=None, dest="auth", action="store_false")
    cert_group = commandline_subparser.add_mutually_exclusive_group()
    cert_group.add_argument("--verify-cert", default=None, dest="verify", action="store_true")
    cert_group.add_argument("--no-verify-cert", default=None, dest="verify", action="store_false")
    redirect_group = commandline_subparser.add_mutually_exclusive_group()
    redirect_group.add_argument("--redirect", default=None, dest="redirect", action="store_true")
    redirect_group.add_argument("--no-redirect", default=None, dest="redirect", action="store_false")
    commandline_subparser.add_argument("--filename", help="Specify output filename.", required=True)
    commandline_subparser.add_argument("--title", default="", help="Specify parsing link name.")
    commandline_subparser.add_argument("--email", default="", help="Specify parsing admin email.")
    commandline_subparser.add_argument("--unit", default="", help="Specify parsing admin unit.")
    return parser.parse_args()

"""
Parse function
"""
def parse_funct(filename, config, logger):
    (session, history, source, linktexts) = Request.initialize(config=config, decode="utf-8")
    if config.depth > 0:
        history.update(Request.navigate(linktexts=linktexts, history=history, config=config, decode="utf-8"))
    Request.file_generator(history=history, config=config, logger=logger, output_filename=filename)
    Request.close()
    quit()

"""
Round function
"""
def round_funct(args, logger):
    if args.subparser_name == "config":
        for tag in args.tags[0:]:
            config = Request.Config(filename=".requests.conf", tag=tag)
            config.load_config()
            parse_funct(tag, config, logger)
    elif args.subparser_name == "commandline":
        filename = args.filename
        config = Request.Config(filename=".requests.conf", tag=args.tag)
        config.load_config()

        if args.auth is not None:
            config.auth = args.auth
        if args.verify is not None:
            config.verify = args.verify
        if args.redirect is not None:
            config.follow_redirection = args.redirect
        config.title = args.title
        config.email = args.email
        config.unit = args.unit
        config.target_url = Request.factor_url(args.url, "")
        config.current_url = Request.factor_url(args.url, "")
        config.domain_url = Request.pattern_generator(args.url)

        if args.depth >= 0:
            config.depth = args.depth

        parse_funct(filename, config, logger)

"""
"""
def main():
    argv = sys.argv

    logger = log_initialize("main.log")
    args = arg_initialize(argv)

    round_funct(args, logger)

"""
Main function
"""
if __name__ == "__main__":
    main()
