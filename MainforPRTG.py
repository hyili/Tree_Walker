#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import Request

def main(url):
    # need to specify USER and PASS in your config
    conf = Request.Config(filename=".requests.conf", tag="DEFAULT")
    conf.load_config()

    conf.target_url = Request.factor_url(url, "")
    conf.current_url = Request.factor_url(url, "")
    conf.domain_url = ""
    conf.depth = 0

    (session, history, source, linktexts) = Request.initialize(config=conf, decode="utf-8")
    status_code = history[conf.target_url]["status_code"]
    Request.close()

    return status_code

if __name__ == "__main__":
    status_code = main("https://itriweb.itri.org.tw")
    print(status_code)
