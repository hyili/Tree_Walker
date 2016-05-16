#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import sys
import Request

"""
Main function
"""
def main(argv):
    total_start_time = Request.datetime.datetime.now()
    for tag in argv[1:]:
        print("["+str(tag)+"]\n")
        conf = Request.load_conf(filename=".requests.conf", tag=tag)

        session = Request.requests.Session()
        print("************************************************************")
        print(conf["TARGET_URL"])
        print("************************************************************")
        source = Request.authenticate(session=session, payload=conf["PAYLOAD"], target_url=conf["TARGET_URL"], auth=conf["AUTH"])
        linktexts = Request.find_linktexts(source=source)
        if conf["DEPTH"] > 0:
            history = Request.navigate(session=session, multithread=conf["MULTITHREAD"], threshold=conf["THRESHOLD"], linktexts=linktexts, current_url=conf["TARGET_URL"], target_url_pattern=conf["TARGET_URL_PATTERN"], filter_code=conf["FILTER"], timeout=conf["TIMEOUT"], depth=conf["DEPTH"])
        else:
            history = {}
        Request.file_generator(history=history, output_format=conf["FORMAT"], output_filename=tag, filter_code=conf["FILTER"], sort=conf["SORT"])
        session.close()

    total_end_time = Request.datetime.datetime.now()
    print("Total time costs: "+str(float((total_end_time-total_start_time).seconds) + float((total_end_time-total_start_time).microseconds) / 1000000.0)+"sec\n")

if __name__ == "__main__":
    argv = sys.argv

    main(argv)
