#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 16:45:21 2023

@author: saurav
"""

#Installation
#pip install psycopg2
import os
import psycopg2
from urllib.parse import urlparse

class userauthentication:
   def __init__(self,login_name,login_password,insta_account):
        
        self.login_name = login_name  
        self.login_password = login_password  
        self.insta_account = insta_account 
        print(self.login_name)
        if insta_account == '':
           self.insta_account = 'general'
        postgreSQL_select_Query = 'SELECT pg_cancel_backend(pid), pg_terminate_backend(pid) FROM   pg_stat_activity;'   
        self.executequery(postgreSQL_select_Query,'registration')
        
   def executequery(self, query,query_type):
       try: 
           rows = []
           postgreSQL_select_Query = query
           query_type = query_type
           print('stage 1')
           url = urlparse("postgres://uctlimdc:APYB9-l-VwTUIkuRAQG3s4jmfsAGTdlg@rosie.db.elephantsql.com/uctlimdc")
           #url = urlparse("postgres://uctlimdc:APYB9-l-VwTUIkuRAQG3s4jmfsAGTdlg@rosie.db.elephantsql.com/uctlimdc")
           conn = psycopg2.connect(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port )
           cur = conn.cursor()
           print('stage 2')
           cur.execute(postgreSQL_select_Query)
           
           if query_type == 'login':
               rows = cur.fetchall()
    
           #print(self.df) 
           print('stage 3')
           conn.commit()
           conn.close()
       except:
           
           if conn:
              conn.close()
        
       return rows
  
   def LoginCheck(self):
       login_ls=[]
       postgreSQL_select_Query = "select * from users where username = '"+self.login_name+"';"
       
       rows = self.executequery(postgreSQL_select_Query,'login')
       
       
       if rows == []:
           message ='User Not Found'
       
       else:        
           for row in rows:
               login_ls = row
           password = login_ls
            
           self.insta_account = login_ls[4]
           print('password')
           print('login_ls[2]',password)
           if self.login_password == login_ls[2]:
              message = 'Successful Login'
              postgreSQL_select_Query = "update users set remarks='"+message+"' \
              , time=current_timestamp AT TIME ZONE 'Asia/Singapore', date=CURRENT_DATE where username ='"+self.login_name+"';"          
              self.executequery(postgreSQL_select_Query,'registration')
           else:
              login_attempt = login_ls[5]+1
              message = 'Login Failed - Invalid Password!'
              postgreSQL_select_Query = "update users set wrong_login_attempt=wrong_login_attempt+1, remarks='"+message+"' \
              , time=current_timestamp AT TIME ZONE 'Asia/Singapore', date=CURRENT_DATE where username ='"+self.login_name+"';"          
              self.executequery(postgreSQL_select_Query,'registration')
              #return message
              
       return message,self.insta_account
    
   def registration(self):
        row = self.LoginCheck()
        #print(row[0])
        message = row[0]
        print(message)
        if message =='Successful Login':
           message = 'User already exists. Please use login screen to login.'
        
        else:
            postgreSQL_select_Query = "insert into users(username,password,instagram_account) \
            values('"+self.login_name+"','"+self.login_password+"','"+self.insta_account+"');"
        
            #postgreSQL_select_Query ='drop table users;'
            self.executequery(postgreSQL_select_Query,'registration')
        
        return message,self.insta_account   
   
   def py_changepassword(self):
       postgreSQL_select_Query = "update users set old_password=password, password ='"+self.login_password+"', remarks='Password has been changed' \
       , time=current_timestamp AT TIME ZONE 'Asia/Singapore', date=CURRENT_DATE where username ='"+self.login_name+"';" 
       
       
       #postgreSQL_select_Query ='drop table users;'
       self.executequery(postgreSQL_select_Query,'changepassword')
       row = self.LoginCheck()
       message = row[0]
       self.insta_account = row[1]
            
       return message,self.insta_account   
   
   def py_changeinstagram(self):
       postgreSQL_select_Query = "update users set instagram_account ='"+self.insta_account+"', remarks='Instagram account has been changed'\
       , time=current_timestamp AT TIME ZONE 'Asia/Singapore', date=CURRENT_DATE where username ='"+self.login_name+"';" 
       
       
       #postgreSQL_select_Query ='drop table users;'
       self.executequery(postgreSQL_select_Query,'changeinstagram')
       row = self.LoginCheck()
       message = row[0]
       self.insta_account = row[1]
            
       return message,self.insta_account   
    
'''
person1 = userauthentication("life.is.beautiful.com", 'dogsarebeautiful','GoldenRetirever')  

#test = person1.registration()  


test2 = person1.py_changeinstagram()
#message = [test2]
print(test2[0],test2[1])'''