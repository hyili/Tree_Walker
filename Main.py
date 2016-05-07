#!/usr/bin/python
# -*- coding: utf-8 -*-

import Request

"""
Main function
"""
def main():
    conf = Request.load_conf(".requests.conf", "PROFILE")
    filter_code = [int(i) for i in conf["FILTER"].split(",")]
    payload = {"target": conf["TARGET_URL"], "USER": conf["USER"], "PASSWORD": conf["PASS"]}
    history = {}
    session = Request.requests.Session()

    print "************************************************************"
    print conf["TARGET_URL"]
    print "************************************************************"
    total_start_time = Request.datetime.datetime.now()
    if conf["AUTH"] == "YES":
        source = Request.authenticate(session, conf["TARGET_URL"], payload)
    else:
        source = session.get(conf["TARGET_URL"]).text
    linktexts = Request.find_linktexts(source)
    Request.navigate(session, conf["TARGET_URL_PATTERN"], conf["TARGET_URL"], linktexts, history, filter_code, timeout=conf["TIMEOUT"], depth=conf["DEPTH"]-1)
    Request.file_generator(conf["FORMAT"], history, filter_code, conf["SORT"], conf["FILENAME"])
    total_end_time = Request.datetime.datetime.now()
    print "Total time costs: "+str(float((total_end_time-total_start_time).seconds) + float((total_end_time-total_start_time).microseconds) / 1000000.0)+"sec\n"
    session.close()

if __name__ == "__main__":
    main()
