# -*- coding: utf-8 -*-
'''
爬虫网易云，可获得单首音乐的评论
@author: WXC
'''

import requests,json,os
import base64
import codecs
from Crypto.Cipher import AES
import pymysql
import random
import time

###########修改mySpiderSongId的值即可爬取另一首歌的评论信息##############
mySpiderSongId = '418603077'
mySpiderSong = 'spider_'+mySpiderSongId
 
#这是获取两个参数的类
class WangYiYun():
    
    def __init__(self):
        
        #在网易云获取的四个参数
        self.first_param = '{rid: "R_SO_4_'+ mySpiderSongId +'", offset: "9360", total: "true", limit: "20", csrf_token: ""}'
        self.second_param = '010001'
        self.third_param = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.fourth_param = '0CoJUm6Qyw8W8jud'
        
    def create_random_16(self):
        #获取随机十六个字母拼接成的字符串
        return (''.join(map(lambda xx: (hex(ord(xx))[2:]), str(os.urandom(16)))))[0:16]
        
    def aesEncrypt(self, text, key):
        #偏移量
        iv = '0102030405060708'
        #文本
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key, 2, iv)
        ciphertext = encryptor.encrypt(text)
        ciphertext = base64.b64encode(ciphertext)
        return ciphertext
    
    def get_params(self, text, page):
        global textPublic
        textPublic = self.create_random_16()
        #获取第一个参数
        #text = self.create_random_16()
        text = textPublic
        
        if page==1:
            self.first_param = '{rid: "R_SO_4_'+ mySpiderSongId +'", offset: "0", total: "true", limit: "20", csrf_token: ""}'
        else:
            self.first_param = ('{rid: "R_SO_4_'+ mySpiderSongId +'", offset:%s, total: "false", limit: "20", csrf_token: ""}'%str((page-1)*20))
        
        params = self.aesEncrypt(self.first_param, self.fourth_param).decode('utf-8')
        params = self.aesEncrypt(params, text)
        return params
    
    def rsaEncrypt(self, pubKey, text, modulus):
        #进行rsa加密
        text = text[::-1]
        rs = int(codecs.encode(text.encode('utf-8'), 'hex_codec'), 16) ** int(pubKey, 16) % int(modulus, 16)
        return format(rs, 'x').zfill(256)
    
    def get_encSEcKey(self, text):
        #获取第二个参数
        #text = self.create_random_16()
        text = textPublic
        pubKey = self.second_param
        modulus = self.third_param
        encSecKey = self.rsaEncrypt(pubKey, text, modulus)
        return encSecKey

#这是解析网易云音乐和获取评论的类
class Spider():

    def __init__(self):
        
        self.header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
                       'Referer': 'http://music.163.com/'}
        self.url = 'https://music.163.com/weapi/v1/resource/comments/R_SO_4_'+ mySpiderSongId +'?csrf_token='
        
    def __get_jsons(self, url, page):
        # 获取两个参数
        music = WangYiYun()
        text = music.create_random_16()
        params = music.get_params(text, page)
        encSecKey = music.get_encSEcKey(text)
        fromdata = {'params': params,'encSecKey': encSecKey}
        
        #proxie = ipProxies()
        
        proxieList = [{'http':'http://122.114.31.177:808'}, {'http':'http://61.135.217.7:80'}, {'http':'http://125.118.76.229:808'}, {'http':'http://122.241.73.82:808'},
                      {'http':'http://115.154.191.26:80'}, {'http':'http://111.155.116.211:8123'}, {'http':'http://125.122.168.55:808'},{'http':'http://110.73.0.57:8123'}]
        randomProxie = random.choice(proxieList)
        print('-------------go go go-------------')
        print('代理ip:'+randomProxie['http'])
    
        time.sleep(random.randint(5,30))
        jsons = requests.post(url, data=fromdata, proxies=randomProxie, headers=self.header)
        #print('jsons.status_code：',jsons.status_code)
        #打印返回来的内容，是个json格式的
        #print(jsons.content)
        return jsons.text
        
    def json2list(self, jsons):
        '''
        #把json转成字符串，并把它重要的信息获取出来存入列表
        #print(json.loads(jsons.text))#用json.loads()把它转成字典
        #print(type(users))
        #print(users)
        '''
        users = json.loads(jsons)
        comments = []
        #print(users)
        for user in users['comments']:
            #print(user['user']['nickname']+' : '+user['content']+' 点赞数：'+str(user['likedCount']))
            userId = user['user']['userId']#1用户id
            nickname = user['user']['nickname']#2用户昵称
            content = user['content']#3评论内容
            time = user['time']#4评论时间
            likedCount = user['likedCount']#5评论被点赞数
            beReplied = len(user['beReplied'])#6评论被回复
            user_dict =  {'userId': userId, 'nickname': nickname, 'content': content, 'time': time, 'likedCount': likedCount, 'beReplied': beReplied}
            comments.append(user_dict)
        return comments
    
    def write2sql(self,comments):
        '''把评论写入数据库'''
        music = Operate_SQL()
        print('第%d页正在获取' % self.page)
        for comment in comments: 
            timeStamp = float(comment['time']/1000)
            timeArray = time.localtime(timeStamp)
            comment['time'] = time.strftime("%Y-%m-%d %H:%M:%S", timeArray) 
            music.add_data(comment)
        print('   该页获取完成')
    
    def run(self):
        self.page = 1
        while True:
            jsons = self.__get_jsons(self.url, self.page)
            comments = self.json2list(jsons)
            #当这一页的评论数少于20条时，证明已经获取完
            self.write2sql(comments)
            if len(comments) < 20:
                print('评论已经获取完')
                break
            self.page += 1

# 操作 mysql
class Operate_SQL():
    # 连接数据库
    def __get_conn(self):
        try:
            # 我用的的本地数据库，所以host是127.0.0.1
            self.conn = pymysql.connect(host='127.0.0.1',user='root',passwd='931022',port=3306,db='music',charset='utf8mb4')
        except Exception as e:
            print(e, '数据库连接失败')

    def __close_conn(self):
        '''关闭数据库连接'''
        try:
            if self.conn:
                self.conn.close()
        except pymysql.Error as e:
            print(e, '关闭数据库失败')

    def add_data(self,comment):
        '''增加一条数据到数据库'''
        sql = 'INSERT INTO `'+mySpiderSong+'`(`userId`,`nickname`,`content`,`time`,`likedCount`,`beReplied`) VALUE(%s,%s,%s,%s,%s,%s)'
        try:
            self.__get_conn()
            cursor = self.conn.cursor()
            cursor.execute(sql, (comment['userId'],comment['nickname'],comment['content'],comment['time'],comment['likedCount'],comment['beReplied']))
            self.conn.commit()
            return 1
        except AttributeError as e:
            print(e,'添加数据失败')
            # 添加失败就倒回数据
            self.conn.rollback()
            return 0
        except pymysql.DataError as e:
            print(e)
            self.conn.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()
            self.__close_conn()

##################初始建表语句##################
def create_table():    
    #自动建表语句
    db = pymysql.connect("localhost","root","931022","music" ) 
    
    cursor = db.cursor()   
    sql0 = """CREATE TABLE """+mySpiderSong+""" ( 
             userId INT(11), 
             nickname VARCHAR(60), 
             content VARCHAR(280), 
             time VARCHAR(19), 
             likedCount INT(11), 
             beReplied INT(1))"""  
    cursor.execute(sql0)  
    print("CREATE TABLE OK")  
    #关闭数据库连接  
    db.close()    
##################初始建表语句##################
    
def main():
    #create_table()
    spider = Spider()
    spider.run()
    
main()