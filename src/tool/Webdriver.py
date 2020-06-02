#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ChromeDriver():
    def __init__(self):
        self.wd = None
    
    def init_webdriver(self, cookies=None, driver_location="/usr/local/bin/chromedriver", verify=False):
        if self.wd is None:
            # Authentication session synchronization between requests and selenium problem. Done
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--ssl-protocol=any")
            chrome_options.add_argument(f"--ignore-ssl-errors={str(not verify).lower()}")
            self.wd = webdriver.Chrome(executable_path=driver_location, chrome_options=chrome_options)

            # init
            self.wd.get("https://itriforms.itri.org.tw/itrisso_login.fcc")

            # set cookies
            if cookies is not None:
                for cookie in cookies:
                    self.wd.add_cookie(cookie.__dict__)
    
    def run_webdriver(self, url, timeout):
        self.wd.set_page_load_timeout(timeout)
        self.wd.set_script_timeout(timeout)
    
        try:
            self.wd.get(url)
            time.sleep(timeout)
            result = self.wd.current_url
            if self.wd.current_url == "about:blank":
                result = url
        except:
            result = url
        finally:
            return result
    
    def close_webdriver(self):
        self.wd.quit()
