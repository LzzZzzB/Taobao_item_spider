import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo


client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)


#搜索函数，找到搜索框和按钮，输入搜索关键词，获取第一页的商品信息
def search():
    print("正在搜索...")
    try:
        browser.get('http://www.taobao.com') #源码
        #判断是否加载成功
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q')) #确认输入框加载完毕
        )
        submit = wait.until(                #确认按钮加载完毕
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        input.send_keys(KEYWORD)    #输入关键字
        submit.click()              #点击
        total = wait.until(         #确认商品列表加载完毕
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        get_prodecuts()             #调用get_product获取商品信息
        return total.text           #search()返回页数
    except TimeoutException:
        return search()             #如果发生错误超时，则继续迭代搜索


#获取下一页，实现翻页目的
def next_page(page_number):
    print("正在翻页：",page_number) #打印以作测试用途
    try:        #找到输入框和按钮
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number))
        )
        get_prodecuts()
    except TimeoutException:
        return next_page()


#获取页面的商品的信息
def get_prodecuts():    #确认商品信息加载完毕
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
        )
    html = browser.page_source  #获取源码
    doc = pq(html)          #pyquery化
    items = doc('#mainsrp-itemlist .items .item').items()   #items()获取全部信息
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),        #image在 class=pic > class=img 的'arc'属性下
            'price': item.find('.price').text(),                #price在 class=price 下，用text()获取文本
            'deal': item.find('.deal-cnt').text()[:-3],         #同上获取文本，用切片删掉后面三个字
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)          #调用save_to_mongo() 将product存入数据库

def save_to_mongo(result):
    try:
        if db[MONG0_TABLE].insert(result):      #存入数据库
            print("存储到MONGODB成功~！",result)
    except Exception:
        print("存储到MONGODB失败。。。",result)


#整个爬虫的调度
def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1)) #获取total里面的数字（\d+），转化为int
        #print(total)
        #print(type(total))
        for i in range(2, total+1):     #翻页从第二页开始
            next_page(i)                #页码作为参数传到next_page()
    except Exception:
        print("出错啦~")
    finally:
        browser.close()                 #finally，无论如何最后关闭浏览器


if __name__ == '__main__':
    main()