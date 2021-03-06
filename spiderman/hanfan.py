#/usr/bin/env python
#coding=utf8
"""
# Author: kellanfan
# Created Time : Tue 29 Jan 2019 06:53:36 PM CST

# File Name: hanfan.py
# Description:

"""
import os, sys, time
import redis
from lxml import etree
from misc.openurl import OpenUrl
from misc import pg_client
from log.create_logger import create_logger
logger = create_logger()
class Hanfan(object):
    def __init__(self):
        self.__redis_link = self.__redis_connect()
        self.pg_connect = pg_client.Mypostgres()
        self.main_url = 'https://www.hanfan.cc/'

    def __redis_connect(self):
        pool = redis.ConnectionPool(host='192.168.1.7',port=6379)
        return redis.Redis(connection_pool=pool)
    
    def get_url(self, ftype):
        ourl = OpenUrl(self.main_url + ftype)
        code,main_content = ourl.run()
        if code == 200:
            selecter = etree.HTML(main_content)
            pages = int(selecter.xpath('/html/body/section/div[1]/div/div[2]/ul/li[8]/span/text()')[0].split(' ')[1])
        else:
            logger.error("bad url: %s" %self.main_url)
            sys.exit()

        for page in range(1,pages):
            page_url = self.main_url + ftype + '/page/%s/'%page
            sub_ourl = OpenUrl(page_url)
            sub_code,sub_content = sub_ourl.run()
            if sub_code == 200:
                selecter = etree.HTML(sub_content)
                selecter_list = selecter.xpath('//article/header/h2/a')
                for link in selecter_list:
                    name = link.text
                    sub_url = link.attrib['href'] + '#prettyPhoto/0/'
                    self.__redis_link.set(name, sub_url, ex=21600)
            else:
                logger.error('[%s] can not open...'%page_url)
                continue

            time.sleep(1)
                    
    def get_download_url(self):
        redis_keys = self.__redis_link.keys()
        for fkey in redis_keys:
            url = self.__redis_link.get(fkey)
            ourl = OpenUrl(url)
            code,content = ourl.run()
            if code == 200:
                selecter = etree.HTML(content)
                try:
                    cloudpan_url = selecter.xpath('//div[@class="part"]/a/@href')
                    if len(cloudpan_url) == 1:
                        cloudpan_url = cloudpan_url[0]
                        cloudpan_pass = selecter.xpath('//div[@class="part"]/text()')[2]
                    elif len(cloudpan_url) == 2:
                        cloudpan_url = '|'.join(cloudpan_url)
                        cloudpan_pass = '|'.join(selecter.xpath('//div[@class="part"]/text()')[2:4])
                    else:
                        logger.error('[{}] donot has cloudpan download link...'.format(fkey.decode()))
                        continue
                except:
                    logger.error('[{}] miss something..'.format(fkey.decode()))
                    continue
                self.send_pg([fkey, cloudpan_url, cloudpan_pass])
            else:
                logger.error('[%s] can not open the download page..'%fkey.decode())
                continue
            time.sleep(0.5)

    def send_pg(self, para):
        sql = "insert into hanfan(name,url,panpass) values (%s,%s,%s)"
        ret = self.pg_connect.execute(sql)
        if ret:
            logger.info('insert [{}] ok...'.format(para))
        else:
            logger.error("insert [{}] failed: [{ret}]".format(para, ret))

if __name__ == '__main__':
    a = Hanfan()
    for i in ['variety', 'movie', 'hanju']:
        a.get_url(i)
    a.get_download_url()