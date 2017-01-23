#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import lxml.html
import time

import context
import Request
import ConfigLoader


def main():
    while(True):
        """
        web source
        """
        # TODO: set option
        config = ConfigLoader.Config(filename="../sample/config/.requests.conf", tag="WEBCHECK")
        config.load_config()
        admins = config.admin_email
        (session, history, source, linktexts) = Request.initialize(config=config, decode="utf-8-sig")
        if history[config.target_url]["status_code"] == 200:
            print("OK")
        else:
            print(history[config.target_url]["status_code"])
            print(history[config.target_url]["reason"])
            quit()

        """
        test: file source
        """
#       source_file = open("./hello.html", 'r', encoding='utf-8-sig')
#       source = source_file.read()
#       source_file.close()

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
                for admin in admins:
                    mailcc += admin + ";"
                print(mailcc)
                unit = root.get_element_by_id(i)[4].text_content()
                print(unit)
                level = "0"
                empno = "WebCheck"

                Request.history_in_queue.put({"url": "http://localhost:5000/exec?title="+title+"&url="+url+"&mailto="+mailto+"&mailcc="+mailcc+"&unit="+unit+"%level="+level+"&empno="+empno, "timeout": config.timeout, "header": config.header})  #  TODO: level, empno
            except KeyError as e:
                print("No such id")
                print(str(e))
                break

            if i % 5 == 0:
                time.sleep(5)

            i += 1

        if i != 1:
            receiver = ""
            for admin in admins:
                receiver += admin + ";"
            print("Send Report.")
            Request.history_in_queue.put({"url": "http://localhost:5000/send_report?title=Send_Report&mailto="+receiver, "timeout": config.timeout, "header": config.header})
            time.sleep(20)
            Request.close()
            quit()
        else:
            continue

if __name__ == "__main__":
    main()
