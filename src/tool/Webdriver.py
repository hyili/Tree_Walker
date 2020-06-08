#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
##from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class ChromeDriver():
    def __init__(self, cookies=None, verify=False, driver_location="/usr/local/bin/chromedriver"):
        self.wd = None
        self.cookies = cookies
        self.verify = verify
        self.driver_location = driver_location
    
    def init_webdriver(self):
        if self.wd is None:
            ##caps = DesiredCapabilities.CHROME
            ##caps['goog:loggingPrefs'] = {'performance': 'ALL'}

            # Authentication session synchronization between requests and selenium problem. Done
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--ssl-protocol=any")
            chrome_options.add_argument(f"--ignore-ssl-errors={str(not self.verify).lower()}")
            ##self.wd = webdriver.Chrome(executable_path=self.driver_location, chrome_options=chrome_options, desired_capabilities=caps)
            self.wd = webdriver.Chrome(executable_path=self.driver_location, chrome_options=chrome_options)
            self.wd.set_window_size(1920, 1080)

            # init
            self.wd.get("https://itriforms.itri.org.tw/itrisso_login.fcc")

            # set cookies
            if self.cookies is not None:
                for cookie in self.cookies:
                    self.wd.add_cookie(cookie.__dict__)
    
    def run_webdriver(self, url, timeout, save_screenshot=False):
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

        # get size of scrollWidth & scrollHeight in html tag, then save screenshot
        try:
            if save_screenshot:
                scroll_width = max(self.wd.execute_script("return document.body.parentNode.scrollWidth"), 1920)
                scroll_height = max(self.wd.execute_script("return document.body.parentNode.scrollHeight"), 1080)
                self.wd.set_window_size(scroll_width, scroll_height)
                screenshot_PNG = self.wd.get_screenshot_as_png()
            else:
                screenshot_PNG = None
        except:
            screenshot_PNG = None

        return result, screenshot_PNG
    
    def close_webdriver(self):
        self.wd.quit()
