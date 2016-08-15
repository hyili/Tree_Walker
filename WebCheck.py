#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import Request
import lxml.html
import time

def main():
    """
    web source
    """
    conf = Request.Config(filename=".requests.conf", tag="WEBCHECK")
    conf.load_config()
    (session, history, source, linktexts) = Request.initialize(config=conf, decode="utf-8")
    if history[conf.target_url]["status_code"] == 200:
        print("OK")
    else:
        quit()

    """
    test: file source
    """
#    source_file = open("./hello.html", 'r', encoding='utf-8')
#    source = source_file.read()
#    source_file.close()

    i = 1
    root = lxml.html.fromstring(source)
    while(True):
        try:
            title = root.get_element_by_id(i)[0].text_content()
            print(title)
            url = root.get_element_by_id(i)[1].text_content()
            print(url)
            mailto = root.get_element_by_id(i)[2].text_content()+";"
            print(mailto)
            mailcc = root.get_element_by_id(i)[3].text_content()+";"
            print(mailcc)
            unit = root.get_element_by_id(i)[4].text_content()
            print(unit)

            Request.history_in_queue.put({"url": "http://localhost:5000/exec?title="+title+"&url="+url+"&mailto="+mailto+"&mailcc="+mailcc+"&unit="+unit, "timeout": conf.timeout, "header": conf.header})
        except KeyError as e:
            print("No such id")
            print(str(e))
            break

        if i % 5 == 0:
            time.sleep(5)

        i += 1

    Request.close()
    quit()

if __name__ == "__main__":
    main()
