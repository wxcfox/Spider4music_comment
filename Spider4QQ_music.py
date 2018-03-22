# coding=utf-8
import time
from lxml import etree
import requests
from selenium import webdriver
import pymysql

mySpiderSong='qq1'
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
#        sql = 'INSERT INTO `'+mySpiderSong+'`(`userId`,`nickname`,`content`) VALUE(%s,%s,%s)'
        sql = 'INSERT INTO `'+mySpiderSong+'`(`userId`,`nickname`,`content`,`time`,`likedCount`,`beReplied`) VALUE(%s,%s,%s,%s,%s,%s)'
        try:
            self.__get_conn()
            cursor = self.conn.cursor()
#            cursor.execute(sql, (comment['userId'],comment['nickname'],comment['content']))
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


#driver = webdriver.Firefox()
driver = webdriver.Firefox()
url='https://y.qq.com/n/yqq/song/003OUlho2HcRHC.html'
driver.get(url)
#driver.switch_to.frame(driver.find_element_by_name("contentFrame"))

com_list={418603077}
#==============================================================================
user_dict={}
comments = []

response= etree.HTML(driver.page_source)

a='回复'
def sprider_page():
    for i in range(1,26):
        try:
            userId='%s'%i
            nickname=response.xpath('//*[@id="comment_box"]/div[4]/ul/li[%s]/h4/a/text()'%i)[0]
            content=response.xpath('//*[@id="comment_box"]/div[4]/ul/li[%s]/p/text()'%i)[0]
            time=response.xpath('//*[@id="comment_box"]/div[4]/ul/li[%s]/div[1]/span/text()'%i)[0]
            likedCount=response.xpath('//*[@id="comment_box"]/div[4]/ul/li[%s]/div[1]/a[1]/span/text()'%i)[0]
            if a in content:
                beReplied=1
            else:
                beReplied=0
            #user_dict =  {'userId': userId, 'nickname': nickname,'content': content}
            user_dict =  {'userId': userId, 'nickname': nickname, 'content': content, 'time': time, 'likedCount': likedCount, 'beReplied': beReplied}
            comments.append(user_dict)
        except IndexError as e:
            print('IndexError!')
            
    print('#################')
    print (comments)

    music = Operate_SQL()
    for comment in comments:
        music.add_data(comment)
    print('该页获取完成')
    
    
sprider_page()
driver.find_element_by_xpath('//*[@id="comment_box"]/div[4]/div[2]/a[5]/span').click()
time.sleep(10)

sprider_page()
driver.find_element_by_xpath('//*[@id="comment_box"]/div[4]/div[2]/a[6]/span').click()
time.sleep(10)

sprider_page()
driver.find_element_by_xpath('//*[@id="comment_box"]/div[4]/div[2]/a[7]/span').click()
time.sleep(10)

while(1):
    driver.find_element_by_xpath('//*[@id="comment_box"]/div[4]/div[2]/a[8]/span').click()
    sprider_page()
    time.sleep(10)
#    except NoSuchElementException as e: 
#        print('NoSuchElementException!')
        