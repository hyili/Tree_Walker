#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import sys
import Request

"""
Main function
"""
def round_funct(argv):
    total_start_time = Request.datetime.datetime.now()
    for tag in argv[1:]:
        history = {}
        source = ""
        linktexts = []

        print("["+str(tag)+"]")
        conf = Request.load_conf(filename=".requests.conf", tag=tag)

        session = Request.requests.Session()
        print("************************************************************")
        print(conf.target_url)
        print("************************************************************")
        (source, history) = Request.authenticate(session=session, payload=conf.payload, filter_code=conf.filter_code, target_url=conf.target_url, auth=conf.auth)
        linktexts = Request.find_linktexts(source=source)
        if conf.depth > 0:
            history.update(Request.navigate(session=session, multithread=conf.multithread, threshold=conf.threshold, linktexts=linktexts, filter_code=conf.filter_code, current_url=conf.target_url, domain_url=conf.domain_url, timeout=conf.timeout, depth=conf.depth))
        Request.file_generator(history=history, filter_code=conf.filter_code, output_format=conf.output_format, output_filename=tag, sort=conf.sort)
        session.close()

    total_end_time = Request.datetime.datetime.now()
    print("Total time costs: "+str(float((total_end_time-total_start_time).seconds) + float((total_end_time-total_start_time).microseconds) / 1000000.0)+"sec\n")

if __name__ == "__main__":
    argv = sys.argv

    round_funct(argv)
