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
    ITSMserver = DBconfig.get('ITSM', 'SERVER').replace("\'","")
    ITSMusername = DBconfig.get('ITSM', 'USERNAME').replace("\'","")
    ITSMpassword = DBconfig.get('ITSM', 'PASSWORD').replace("\'","")
    ITSMdatabase = DBconfig.get('ITSM', 'DATABASE').replace("\'","")
    ITSMport = DBconfig.get('ITSM', 'PORT').replace("\'","")
    #"""
    
    #"""
    SDBserver = DBconfig.get('DB', 'SERVER').replace("\'","")
    SDBusername = DBconfig.get('DB', 'USERNAME').replace("\'","")
    SDBpassword = DBconfig.get('DB', 'PASSWORD').replace("\'","")
    SDBdatabase = DBconfig.get('DB', 'DATABASE').replace("\'","")
    SDBport = DBconfig.get('DB', 'PORT').replace("\'","")
    #"""
    
    #"""
    COMMONserver = DBconfig.get('COMMON', 'SERVER').replace("\'","")
    COMMONusername = DBconfig.get('COMMON', 'USERNAME').replace("\'","")
    COMMONpassword = DBconfig.get('COMMON', 'PASSWORD').replace("\'","")
    COMMONdatabase = DBconfig.get('COMMON', 'DATABASE').replace("\'","")
    COMMONport = DBconfig.get('COMMON','PORT').replace("\'","")
    #"""
    
    #先把boss資料存下來
    #common資料
    #COMMON_boss=[]
    COMMONconn = pymssql.connect(server=COMMONserver, user=COMMONusername, port=COMMONport, password=COMMONpassword, database=COMMONdatabase)
    COMMONcur = COMMONconn.cursor(as_dict=True)
    COMMONsql = "SELECT [empno], [Boss_Empno] FROM v_BossEmpno_ByDept"
    COMMONcur.execute(COMMONsql)
    COMMON_boss = {"user":"boss"}
    for r in COMMONcur:
        COMMON_boss.update({r['empno']:r['Boss_Empno']})
    COMMONcur.close()
    COMMONconn.close()
    
    
    #取出所有人的mail資料
    ITSMconn = pymssql.connect(server=ITSMserver, user=ITSMusername, port=ITSMport, password=ITSMpassword, database=ITSMdatabase)
    USRcur = ITSMconn.cursor()
    USRsql = "SELECT [USR_ID], [USR_EMAIL], [USR_NAME] FROM ITSM_AC_OU_USER_V";
    USRcur.execute(USRsql)
    USR_MAIL = {"user":"mail"}
    USR_NAME = {"user":"name"}
    for r in USRcur:
        USR_MAIL.update({r[0]:r[1]})
        USR_NAME.update({r[0]:r[2]})
    USRcur.close()
    ITSMconn.close()

    #"""
    #先取出系統負責人的服務資料
    #print(server+ " " + username + " " + password + " " + database)
    ITSMconn = pymssql.connect(server=ITSMserver, user=ITSMusername, port=ITSMport, password=ITSMpassword, database=ITSMdatabase)
    #print(ITSMconn)
    ITSMcur = ITSMconn.cursor(as_dict=True)
    #ITSMsql = "SELECT S.[CI_UID], S.[NAME], S.[STATUS], S.[A-20150617-00010],S.[A-20150617-00011], O.[OWNER_NAME], O.[OWNER_ID] FROM vwCI_TYPE_Service as S, vwCI_OWNER as O WHERE S.[CI_UID] = O.[CI_UID] and O.[OWNER_TYPE]= 'M' and (S.[CI_UID]='CI-2015063014-000001' or S.[CI_UID]='CI-2015063014-000002')"
    ITSMsql = "SELECT S.[CI_UID], S.[NAME], S.[STATUS], S.[A-20150617-00010],S.[A-20150617-00011], O.[OWNER_NAME], O.[OWNER_ID] FROM vwCI_TYPE_Service as S, vwCI_OWNER as O WHERE S.[CI_UID] = O.[CI_UID] and O.[OWNER_TYPE]= 'M'"
    #ITSMsql = "SELECT S.[CI_UID], S.[NAME], S.[STATUS], S.[A-20150617-00010],S.[A-20150617-00011], O.[OWNER_NAME], O.[OWNER_ID], M.[USR_EMAIL] FROM vwCI_TYPE_Service as S, vwCI_OWNER as O, ITSM_AC_OU_USER_V as M WHERE S.[CI_UID]= O.[CI_UID] and O.[OWNER_TYPE]= 'M' and M.[USR_ID]=O.[OWNER_ID]";

    ITSMcur.execute(ITSMsql)
    
    ITSM_Service=[]
    #先把資料存到陣列裡
    for r in ITSMcur:
        tempArray = []
        ciuid = r['CI_UID']
        name = r['NAME']
        status = r['STATUS'] 
        url1 = r['A-20150617-00010'] 
        url2 = r['A-20150617-00011'] 
        ownername = r['OWNER_NAME'] 
        ownerid = r['OWNER_ID']
        #get user mail
        usermail = USR_MAIL.get(ownerid.strip())
        bossid = COMMON_boss.get(ownerid.strip())
        bossname = USR_NAME.get(bossid.strip())
        bossmail = USR_MAIL.get(bossid.strip()) #確保空格不會影響
        #status規則：如果上線(0)，但SDB沒有，就新增；如果SDB有，且CIUID/NAME跟SDB不同，就修改；
        #如果下線(1)，但SDB有，就把SDB的上/下線狀態改為下線
        tempArray.append(ciuid) 
        tempArray.append(name) 
        tempArray.append(status)
        tempArray.append(url1)
        tempArray.append(url2)
        tempArray.append(ownername)
        tempArray.append(ownerid)
        tempArray.append(usermail)
        tempArray.append(bossname)
        tempArray.append(bossid.strip())
        tempArray.append(bossmail)
        ITSM_Service.append(tempArray)
 
    ITSMcur.close()
    ITSMconn.close()
    #"""    
    """
    #先用測試的
    ITSM_Service=[]
    #第一組正確
    tempArray = ["U1","hk4","0","http://translate.google.com.tw/?hl=zh-TW","","A2","777"]
    ITSM_Service.append(tempArray)
    #第二組CI正確 其他錯誤
    tempArray = ["CI-2015063014-000230","改中文","0","aa","aaw","馬宗琪","890657"]
    ITSM_Service.append(tempArray)
    """
    #連線SDB
    SDBconn = pymssql.connect(server=SDBserver, port=SDBport, user=SDBusername, password=SDBpassword, database=SDBdatabase, charset='utf8' )
    SDBcur = SDBconn.cursor(as_dict=True)
    for r in ITSM_Service:
        new_ciuid = r[0]
        newNo = 1
        if(r[4] =="無" or r[4]==""): #1個網址 檢查一次
            #如果網址有分號
            if(r[3].find(";")>0):
                for urltmp in r[3].split(";"):
                    new_ciuid = r[0]+"-"+str(newNo)
                    sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                    SDBcur.execute(sql)
                    resultsall = SDBcur.fetchone()
                    updateSql = checkFunction(new_ciuid,r[1],r[2],urltmp,r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                    SDBcur.execute(updateSql)
                    newNo += 1
            #如果網址有逗號
            elif(r[3].find(",")>0):
                for urltmp in r[3].split(","):
                    new_ciuid = r[0]+"-"+str(newNo)
                    sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                    SDBcur.execute(sql)
                    resultsall = SDBcur.fetchone()
                    updateSql = checkFunction(new_ciuid,r[1],r[2],urltmp,r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                    SDBcur.execute(updateSql)
                    newNo += 1
            else: #正常 只有一個
                new_ciuid = r[0]+"-"+str(newNo)
                sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                SDBcur.execute(sql)
                resultsall = SDBcur.fetchone()
                newNo += 1
                updateSql = checkFunction(new_ciuid,r[1],r[2],r[3],r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                #print(updateSql)
                SDBcur.execute(updateSql)
        else: #有兩個網址.檢查兩個
            #先檢查第一個
            #如果網址有分號
            #print(r[0])
            #print(newNo)
            if(r[3].find(";")>0):
                for urltmp in r[3].split(";"):
                    new_ciuid = r[0]+"-"+str(newNo)
                    sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                    SDBcur.execute(sql)
                    resultsall = SDBcur.fetchone()
                    updateSql = checkFunction(new_ciuid,r[1],r[2],urltmp,r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                    SDBcur.execute(updateSql)
                    newNo += 1
            #如果網址有逗號
            elif(r[3].find(",")>0):
                for urltmp in r[3].split(","):
                    new_ciuid = r[0]+"-"+str(newNo)
                    sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                    SDBcur.execute(sql)
                    resultsall = SDBcur.fetchone()
                    updateSql = checkFunction(new_ciuid,r[1],r[2],urltmp,r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                    SDBcur.execute(updateSql)
                    newNo += 1
            else: #正常 只有一個
                new_ciuid = r[0]+"-"+str(newNo)
                sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                SDBcur.execute(sql)
                resultsall = SDBcur.fetchone()
                newNo += 1
                updateSql = checkFunction(new_ciuid,r[1],r[2],r[3],r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                #print(updateSql) 
                SDBcur.execute(updateSql)
            #print(newNo)
            #檢查第二個
            if(r[4].find(";")>0):
                for urltmp in r[4].split(";"):
                    new_ciuid = r[0]+"-"+str(newNo)
                    sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                    SDBcur.execute(sql)
                    resultsall = SDBcur.fetchone()
                    updateSql = checkFunction(new_ciuid,r[1],r[2],urltmp,r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                    SDBcur.execute(updateSql)
                    newNo += 1
            #如果網址有逗號
            elif(r[4].find(",")>0):
                for urltmp in r[4].split(","):
                    new_ciuid = r[0]+"-"+str(newNo)
                    sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                    SDBcur.execute(sql)
                    resultsall = SDBcur.fetchone()
                    updateSql = checkFunction(new_ciuid,r[1],r[2],urltmp,r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                    SDBcur.execute(updateSql)
                    newNo += 1
            else: #正常 只有一個
                new_ciuid = r[0]+"-"+str(newNo)
                sql = "SELECT [SYSNAME],[SYSURL],[CI_STATUS],[OWNER],[OWNERID], [DIRE_USR],[DIREID], [OWNER_MAIL], [DIRE_USR_MAIL], [CMDBSTATUS] FROM [SYSINFO] where [CI_UID]='"+new_ciuid+"'"
                SDBcur.execute(sql)
                resultsall = SDBcur.fetchone()
                updateSql = checkFunction(new_ciuid,r[1],r[2],r[4],r[5],r[6],r[7],r[8],r[9],r[10],resultsall) #name,status,url,on,oid, um,bn,bid,bm
                SDBcur.execute(updateSql)
                newNo += 1
    #檢查完之後 再一起commit
    SDBconn.commit()
    SDBcur.close()
    SDBconn.close()

def checkFunction(new_ciuid, name, status, url, ownername, ownerid, usermail, bossname, bossid, bossmail, resultsall): #name,status,url,on,oid, um,bn,bid,bm
    #print(resultsall)
    updateSql = ""
    needUpdateColumn = []
    newUpdateValue=[]
    #print(str(results)+ " " + str(status)
    if(resultsall is None): #只要服務目錄有的就新增 用狀態擋著
        updateSql = insertSysinfo(new_ciuid, name, status, url, ownername, ownerid, usermail, bossname, bossid, bossmail) #ciuid, name, status,url1,ownername,ownerid
        updateSql += insertSystep(new_ciuid, name, status, url, ownername, ownerid) #新增預設步驟做檢查
        #print("insert(sysinfo)")

    if(resultsall is not None): #有資料才比對 update
        if(name != resultsall['SYSNAME']): #系統名稱不同
            needUpdateColumn.append("SYSNAME") #紀錄要update的欄位
            newUpdateValue.append(name) #紀錄更新值
            #print("update(sysname)")

        if(url != resultsall['SYSURL']):
            needUpdateColumn.append("SYSURL")
            newUpdateValue.append(url)
            #print("update(sysinfo-sysurl1)")
            #第一步驟也要改
            updateSql += updateSystep(new_ciuid, status, url)

        if(str(status)!=str(resultsall['CI_STATUS'])):
            needUpdateColumn.append("CI_STATUS")
            newUpdateValue.append(status)
            #步驟要改為不監測
            updateSql += updateSystep(new_ciuid, status, url)
            #print("update(ci_status)"+"really:"+ str(status)+" old:"+str(resultsall['CI_STATUS']))

        if(str(status)!=str(resultsall['CMDBSTATUS'])):
            needUpdateColumn.append("CMDBSTATUS")
            newUpdateValue.append(status)
            #步驟要改為不監測
            updateSql += updateSystep(new_ciuid, status, url)
            #print("update(ci_status)"+"really:"+ str(status)+" old:"+str(resultsall['CI_STATUS']))


        #reallyOwner = ownername+"("+str(ownerid)+")"
        if(ownername != resultsall['OWNER']):
            needUpdateColumn.append("OWNER")
            newUpdateValue.append(ownername)
        if(ownerid != resultsall['OWNERID']):
            needUpdateColumn.append("OWNERID")
            newUpdateValue.append(ownerid)
            #print("update(owner)")
        #print(bossname)
        #print(bossid)
        #reallyBoss = bossname+"("+str(bossid)+")"
        #print(resultsall['DIRE_USR'])
        if(bossname != resultsall['DIRE_USR']):
            needUpdateColumn.append("DIRE_USR")
            newUpdateValue.append(bossname)
            #print("update(reallyBoss)")
        if(str(bossid) != resultsall['DIRE_USR']):
            needUpdateColumn.append("DIREID")
            newUpdateValue.append(str(bossid))
            #print("update(reallyBoss)")

        if(usermail != resultsall['OWNER_MAIL']):
            needUpdateColumn.append("OWNER_MAIL")
            newUpdateValue.append(usermail)
            #print("update(usermail)")

        if(bossmail != resultsall['DIRE_USR_MAIL']):
            needUpdateColumn.append("DIRE_USR_MAIL")
            newUpdateValue.append(bossmail)
            print("update(bossmail)")

        if(resultsall=="None"):
            print("what problem") #還有甚麼例外情形要查
        
    if(len(needUpdateColumn)>0):
        updateSql += updateQuery("SYSINFO", needUpdateColumn, newUpdateValue, new_ciuid)
        #print(updateSql)
    return updateSql

def updateQuery(tablename, needUpdateColumn, newUpdateValue, ciuid):
    updateSql = "UPDATE SYSINFO set "
    for columnIndex in range(0,len(needUpdateColumn)):
        if(columnIndex == len(needUpdateColumn)-1): #最後一欄
            updateSql += needUpdateColumn[columnIndex]+ " =N'" + newUpdateValue[columnIndex] + "' "
        else:
            updateSql += needUpdateColumn[columnIndex]+ " =N'" + newUpdateValue[columnIndex] + "', "
    updateSql += "WHERE [CI_UID] = N'" + ciuid + "';"

    return updateSql

def insertSysinfo(new_ciuid, name, status, url, ownername, ownerid, usermail, bossname, bossid, bossmail):
    #owner = ownername+"("+ownerid+")"
    #reallyBoss = bossname+"("+str(bossid)+")"
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updateSql = "INSERT INTO [SYSINFO]([CI_UID],[SYSNAME],[CI_STATUS],[SYSURL],[OWNER],[OWNERID],[MOD_DTE],[MOD_USR],[DIRE_USR],[DIREID],[OWNER_MAIL],[DIRE_USR_MAIL],[CMDBSTATUS])"
    updateSql += " VALUES(N'"+new_ciuid+"',N'"+name+"',N'"+status+"',N'"+url+"',N'"+ownername+"',N'"+ownerid+"',N'"+today+"','99',N'"+bossname+"',N'"+bossid+"',N'"+usermail+"',N'"+bossmail+"','"+status+"');"
    #print(updateSql)
    return updateSql

def insertSystep(new_ciuid, name, status, url, ownername, ownerid):
    step_id = new_ciuid + "_1"
    delstamp = ""
    if(status=="0"): delstamp="1"
    else: delstamp="0"
    updateSql = "INSERT INTO [SYSTEP]([STEP_ID],[STEP],[URL],[TIMEWARN],[CONTEXT],[CI_UID],[AUTH],[DEL])"
    updateSql += " VALUES(N'"+step_id+"',N'1',N'"+url+"',N'10','',N'"+new_ciuid+"','YES','"+delstamp+"');"

    #print(updateSql)
    return updateSql

def updateSystep(new_ciuid, status, url):
    step_id = new_ciuid + "_1"
    delstamp = ""
    if(status=="0"): delstamp="1"
    else: delstamp="0"
    updateSql = "UPDATE [SYSTEP] SET [DEL]='"+delstamp+"', [URL]=N'"+url+"' WHERE STEP_ID='"+step_id+"';"

    #print(updateSql)
    return updateSql
    


if __name__ == "__main__":
    main()
