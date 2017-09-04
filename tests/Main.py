#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import sys
import logging
import argparse

#src
import Context
import Request
import Output
import ConfigLoader
from tool import Functions

"""
Logger init
"""
def log_initialize(logpath):
    logger = logging.getLogger("main")
    logger.setLevel(logging.WARNING)
    file_handler = logging.FileHandler(logpath+"/main.log")
    file_handler.setLevel(logging.WARNING)
    # TODO: adjust logger
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
    commandline_subparser.add_argument("--tag", default="COMMANDLINE", help="Template tag for commandline execution.")
    commandline_subparser.add_argument("--url", help="Specify target url.", required=True)
    commandline_subparser.add_argument("--title", default="", help="Specify parsing link name.")
    commandline_subparser.add_argument("--context", default="", help="Specify parsing context.")
    commandline_subparser.add_argument("--timewarn", default="", help="Specify parsing timewarn.")
    commandline_subparser.add_argument("--systep_id", default="", help="Specify parsing systep_id.")
    #commandline_subparser.add_argument("--auth", default="", help="Specify parsing auth.")

    cert_group = commandline_subparser.add_mutually_exclusive_group()
    cert_group.add_argument("--verify-cert", default=None, dest="verify", action="store_true")
    cert_group.add_argument("--no-verify-cert", default=None, dest="verify", action="store_false")
    redirect_group = commandline_subparser.add_mutually_exclusive_group()
    redirect_group.add_argument("--redirect", default=None, dest="redirect", action="store_true")
    redirect_group.add_argument("--no-redirect", default=None, dest="redirect", action="store_false")


    return parser.parse_args()

"""
Parse function
"""
def parse_funct(config, logger, systep_id):
    
	#原本的
    #print("timeout")
    #print(config.timeout) #timeout有寫入
    (session, history, source) = Request.initialize(config=config, decode="utf-8-sig")
    print("history")
    print(history)
    #print("2:")
    #print(history[config.target_url]["status_code"])
    if(history[config.target_url]["status_code"]==200):
        context = history[config.target_url]["context"]
        content_code = Request.compare_content(source, context)
    else:
        content_code = -1

    history[config.target_url]["systep_id"] = systep_id
    history.update(Request.navigate(content_code, history=history, config=config, decode="utf-8-sig"))
    Output.file_generator(history=history, config=config, logger=logger)
    """
    #here mail
    configMail = ConfigLoader.Config(filename="config/.requests.conf", tag="COMMANDLINE_IN")
    configMail.load_config()
    receiver = configMail.user+"@itri.org.tw"
    print(receiver)
    #os.system("./Mail5.py --tag " + config.tag + " --receiver" + receiver +" --systep_id" + systep_id+")"
    """
    Request.close()
    #"""
"""
Round function
"""
def round_funct(args):

    if args.subparser_name == "config":
        for tag in args.tags[0:]:
            config = ConfigLoader.Config(filename="config/.requests.conf", tag=tag)
            config.load_config()
            logger = log_initialize(config.logpath)
            parse_funct(tag, config, logger)
    elif args.subparser_name == "commandline":
        #filename = args.filename
        config = ConfigLoader.Config(filename="config/.requests.conf", tag=args.tag)
        config.load_config()

        if args.verify is not None:
            config.verify = args.verify
        if args.redirect is not None:
            config.follow_redirection = args.redirect
        #去設定config
        config.title = args.title
        config.context = args.context

        config.target_url = Functions.factor_url(args.url, "")
        config.domain_url = Functions.pattern_generator(args.url)
        if(args.timewarn!=""):
            config.timewarn = float(args.timewarn)
        if config.auth == "YES":
            config.auth = True
        else:
            config.auth = False
        #print(config.auth)
        """
        if args.depth >= 0:
            config.depth = args.depth
        """
        systep_id = args.systep_id
        logger = log_initialize(config.logpath)
        parse_funct(config, logger, systep_id)

"""
"""
def main():
    argv = sys.argv
    args = arg_initialize(argv)
    round_funct(args)

"""
Main function
"""
if __name__ == "__main__":
    main()
    quit()
