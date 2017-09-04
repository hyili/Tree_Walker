#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import lxml.html
import time

import Context
import Request
import ConfigLoader
import configparser
import requests

import pymssql  

def main():
    
    #"""
    DBconfig = configparser.ConfigParser()
    DBconfig.read('config/.config.conf')
    server = DBconfig.get('DB', 'SERVER').replace("\'","")
    port = DBconfig.get('DB', 'PORT').replace("\'","")
    username = DBconfig.get('DB', 'USERNAME').replace("\'","")
    password = DBconfig.get('DB', 'PASSWORD').replace("\'","")
    database = DBconfig.get('DB', 'DATABASE').replace("\'","")
    #"""
    #print(server+ " " + username + " " + password + " " + database)
    conn = pymssql.connect(server=server, port=port, user=username, password=password, database=database)
    #print(conn)
    cur = conn.cursor(as_dict=True)
    sqlstr = "SELECT S2.[URL], S2.[CI_UID], S2.[CONTEXT], S2.[AUTH], S2.[TIMEWARN], S2.[ID] FROM SYSINFO as S1, SYSTEP as S2 where S1.[CI_STATUS]=0 and S1.[CI_UID]=S2.[CI_UID] and S2.[DEL]=1"
    #cur.execute('SELECT * FROM SYSTEP')
    cur.execute(sqlstr)
    
    #config = ConfigLoader.Config(filename="config/.requests.conf", tag="COMMANDLINE")
    #config.load_config()
    #Request.initialize(config=config, decode="utf-8-sig")

    #get form information
    
    try:
        for r in cur:
            url = r['URL']
            ciid = r['CI_UID']
            context = r['CONTEXT']
            auth = r['AUTH']
            timewarn = r['TIMEWARN']
            systep_id = r['ID']

            if(auth=="YES"):
                print(url + " " + context + " " + str(auth))
                #Request.GlobalVars.history_in_queue.put({"url": "http://localhost:5000/exec?title="+ciid+"&url="+url+"&context="+context, "timeout": config.timeout, "header": config.header})
                #requests.get("http://localhost:7002/exec?title=sso&url=https://itriforms.itri.org.tw/itrisso_login.fcc&context=&timewarn=20&systep_id=1")
                requests.get("http://localhost:7001/exec?title="+ciid+"&url="+url+"&context="+context+"&timewarn="+str(timewarn)+"&systep_id="+str(systep_id))
                #print("yes")
                #print(Request.GlobalVars.history_in_queue.qsize())
            else:
                print(url + " " + context + " " + str(auth))
                #Request.GlobalVars.history_in_queue.put({"url": "http://localhost:5000/exec?title="+ciid+"&url="+url+"&context="+context, "timeout": config.timeout, "header": config.header})
                requests.get("http://localhost:7002/exec?title="+ciid+"&url="+url+"&context="+context+"&timewarn="+str(timewarn)+"&systep_id="+str(systep_id))
                if(ciid=="sso"): 
                    time.sleep(30) #30秒後再進行下一個
                #print("no")
    except KeyError as e:
        print("No such id")
        print("WebCheck: "+str(e))
        #break



    #Request.close()
    cur.close()
    conn.close()
    quit()


if __name__ == "__main__":
    main()
