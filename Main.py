#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import sys
import Request

"""
Parse function
"""
def parse_funct(tag, conf, logger):
    Request.initialize()
    session = Request.requests.Session()
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

    logger = Request.log_initialize(".requests.log")
    args = Request.arg_initialize(argv)

    #total_start_time = Request.datetime.datetime.now()
    round_funct(args, logger)
    #total_end_time = Request.datetime.datetime.now()
    #print("Total time costs: "+str(float((total_end_time-total_start_time).seconds) + float((total_end_time-total_start_time).microseconds) / 1000000.0)+"sec\n")

"""
Main function
"""
if __name__ == "__main__":
    main()
