#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import time
from selenium import webdriver

"""
- Selenium Web Driver
    - just use selenium for web url after redirecting
"""
def run_webdriver(url, timeout, cookies=None, driver_location="/usr/local/bin/phantomjs", follow_redirection=False, verify=False):
    if not follow_redirection:
        return url

    # Authentication session synchronization between requests and selenium problem. Done
    wd = webdriver.PhantomJS(executable_path=driver_location, service_args=["--ignore-ssl-errors="+str(not verify).lower(), "--ssl-protocol=any"])
    # set cookies
    if cookies is not None:
        for cookie in cookies:
            try:
                wd.add_cookie({"name": cookie.name, "value": cookie.value, "domain": cookie.domain, "path": cookie.path})
            except Exception as e:
                # TODO: Do nothing now
                pass
    # wd = webdriver.Chrome(executable_path="/Users/hyili/Documents/Python/selenium/ChromeDriver/chromedriver")
    wd.set_page_load_timeout(timeout)
    wd.set_script_timeout(timeout)
    try:
        wd.get(url)
        time.sleep(timeout)
        result = wd.current_url
        if wd.current_url == "about:blank":
            result = url
    except:
        result = url
    finally:
        wd.quit()
        return result

