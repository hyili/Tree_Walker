#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-

import lxml.html
import time
import sys

import Context
import Request
import ConfigLoader
import configparser
import requests

import datetime
import pymssql  

def main(): 


    DBconfig = configparser.ConfigParser()
    DBconfig.read('config/.config.conf')
    
    #"""
    SDBserver = DBconfig.get('DB', 'SERVER').replace("\'","")
    SDBusername = DBconfig.get('DB', 'USERNAME').replace("\'","")
    SDBpassword = DBconfig.get('DB', 'PASSWORD').replace("\'","")
    SDBdatabase = DBconfig.get('DB', 'DATABASE').replace("\'","")
    SDBport = DBconfig.get('DB', 'PORT').replace("\'","")
    #"""
    
    #"""
    ITSMserver = DBconfig.get('ITSM', 'SERVER').replace("\'","")
    ITSMusername = DBconfig.get('ITSM', 'USERNAME').replace("\'","")
    ITSMpassword = DBconfig.get('ITSM', 'PASSWORD').replace("\'","")
    ITSMdatabase = DBconfig.get('ITSM', 'DATABASE').replace("\'","")
    ITSMport = DBconfig.get('ITSM', 'PORT').replace("\'","")
    #"""
    
    ITSMconn = pymssql.connect(server=ITSMserver, user=ITSMusername, port=ITSMport, password=ITSMpassword, database=ITSMdatabase)
    #先所有員工撈出來
    ITSMsql = "SELECT [USR_ID],[OU_ID],[USR_TITLE] FROM [ITSM_AC_OU_USER_V] WHERE OU_ID like '170%'"
    ITSMcur = ITSMconn.cursor()
    ITSMcur.execute(ITSMsql)
    empArray = []
    for r in ITSMcur:
        tempArray=[]
        tempArray.append(r[0].strip("")) #usrid

        ouid = r[1].strip("")[3:]
        ouind = ""

        if(ouid.find("000")>=0 and r[2].find("組長")>=0):
            ouid = r[1].strip("")[3:4]

        if(r[2].find("經理")>=0 or r[2].find("組長")>=0):
            ouind = "1"
        else:
            ouind = "0"

        if(ouid.find("A000")>=0 and r[2].find("主任")>=0):
            ouid = "SU"
            ouind = "0"

        if(r[0].strip("")=="A50359"):
            ouid = "SA"
            ouind = "1"
        tempArray.append(ouid)
        tempArray.append(ouind) 
        tempArray.append(r[1].strip("")[3:])
        empArray.append(tempArray) 
    ITSMcur.close()
    ITSMconn.close()

    #print(FinalFinalDict)

    #"""
    #連線SDB
    SDBconn = pymssql.connect(server=SDBserver, port=SDBport, user=SDBusername, password=SDBpassword, database=SDBdatabase, charset='utf8' )
    SDBcur = SDBconn.cursor(as_dict=True)
    updateSql=""
    for temp in empArray:
        empno = temp[0]
        ouid = temp[1]
        ouind = temp[2]
        dept = temp[3]
        SDBcurs = SDBconn.cursor(as_dict=True)
        selectsql = "SELECT [USR_ID] FROM [SYSUSER] where [USR_ID]='"+empno+"'"
        SDBcurs.execute(selectsql)
        result = SDBcurs.fetchone()
        if(result is None):
            updateSql = "INSERT INTO [SYSUSER] ([CLASSID], [CLASSIDEN], [DEPT], [USR_ID]) VALUES('"+ouid+"','"+ouind+"','"+dept+"','"+empno+"')"
        else:
            updateSql = "UPDATE [SYSUSER] SET [CLASSID]='"+ouid+"', [CLASSIDEN]='"+ouind+"', [DEPT]='"+dept+"' WHERE USR_ID='"+empno+"'"
        SDBcurs.close()
        SDBcur.execute(updateSql)
    #一起commit 
    
    SDBconn.commit()
    SDBcur.close()
    SDBconn.close()
    #"""



if __name__ == "__main__":
    main()
