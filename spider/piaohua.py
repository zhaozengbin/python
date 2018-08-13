#/usr/bin/env python
#coding=utf8
"""
# Author: kellanfan
# Created Time : Sat 05 May 2018 09:57:24 AM CST

# File Name: piaohua.py
# Description: 爬取飘花网的电影资源

"""

import re
import time
import sys
#发现re确实不好处理一些特殊的html，改动bs4
from bs4 import BeautifulSoup
from misc import mysql_connect
from misc import openurl

def get_url(ftype):
    '''对于这种临时数据暂时存到文件中'''
    main_url = 'https://www.piaohua.com/html/%s/index.html' %ftype
    ourl = openurl.OpenUrl(main_url)
    code,main_content = ourl.openurl()
    #pages = re.search("共 <strong>(\d+)</strong>页", main_content).group(1)
    if code ==  200:
        soup = BeautifulSoup(main_content)
        pages = soup.strong.string
    else:
        print("bad url: %s" %main_url)
        sys.exit(-1)
    #reg = re.compile(r'<a href="(/html/lianxuju/.+?)"')
    fname = 'url_list_' + ftype +'.txt'
    f = open(fname,'w')
    for page in range(1,int(pages)):
        list_url = 'https://www.piaohua.com/html/%s/list_%d.html' %(ftype, page)
        sub_ourl = openurl.OpenUrl(list_url)
        sub_code,sub_content = sub_ourl.openurl()
        if sub_code == 200:
            #ll = re.findall(reg, sub_content)
            sub_soup = BeautifulSoup(sub_content)
            for link in sub_soup.select('a[class=img]'):
                sub_url = link.get('href')
                if sub_url.startswith('/html/'+ftype ):
                    f.write(sub_url+'\n')
        time.sleep(0.5)
    f.close()
    return f

def get_download_url(file,ftype):
    '''主要函数'''
    #读取文件
    f = open(file,'r')
    for line in f.readlines():
        #读取文件每一行
        line = line.split('\n')[0]
        #构建url
        url = 'https://www.piaohua.com' + line
        #获取html内容
        ourl = openurl.OpenUrl(url)
        code, content = ourl.openurl()
        #初始化list
        list_down = []
        #判断是否正确打开
        if code == 200:
            #反爬虫
            time.sleep(0.5)
            #构建soup
            soup = BeautifulSoup(content,'lxml')
            #获取名称
            name = soup.title.string.split('_')[0]
            #获取a标签的href属性，并去除\r，避免后续处理的麻烦
            for link in soup.find_all('a'):
                url = link.get('href')
                if 'ftp' in url:
                    url = ''.join(url.split())
                    list_down.append(url)
                    print(list_down)
            #构建最后的str
            if list_down != []:
                str_down = '#'.join(list_down)
                send_mysql(name, str_down, ftype)

def send_mysql(name, str_down, ftype):
    '''将数据写入数据库'''
    sql = "insert into piaohua(name, content, type) value ('%s', '%s', '%s')"%(name,str_down,ftype)
    connect = mysql_connect.MysqlConnect('./misc/mysql_data.yaml')
    code = connect.change_data('spiderdata', sql)
    if code == 0:
        print('%s ok'%name)
    else:
        print('%s error,message: %s'%(name, code))


if __name__ == '__main__':
    ftype = input("需要下载的类型:\n<dongzuo,xiju,aiqing,kehuan,juqing,xuannian,wenyi,zhanzheng,kongbu,zainan,lianxuju,dongman>\n:")
    f = get_url(ftype)
    get_download_url('url_list_xiju.txt',ftype)
