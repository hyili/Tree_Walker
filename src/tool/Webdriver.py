#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import time
from selenium import webdriver

"""
- Selenium Web Driver
    - just use selenium for web url after redirecting
"""
def run_webdriver(url, timeout, driver_location="/usr/local/bin/phantomjs", follow_redirection=False, verify=False):
    
    if not follow_redirection:
        print("bye")
        return url
    print("hey")
    # Authentication session synchronization between requests and selenium problem. TODO:
    wd = webdriver.PhantomJS(executable_path=driver_location, service_args=["--ignore-ssl-errors="+str(not verify).lower(), "--ssl-protocol=any"])
    wd = webdriver.Chrome(executable_path="/Users/hyili/Documents/Python/selenium/ChromeDriver/chromedriver")
    wd.set_page_load_timeout(timeout)
    wd.set_script_timeout(timeout)
    try:
        print("wd.21")
        wd.get(url)
        time.sleep(timeout)
        print("wd.24:")
        print(timeout)
        result = wd.current_url
        if wd.current_url == "about:blank":
            result = url
    except:
        print("except")
        result = url
    finally:
        print("final")
        wd.quit()
        return result

