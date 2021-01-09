import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time
import requests

class TempoSpider(scrapy.Spider):
    name = 'tempo'
    allowed_domains = ['tempo.com.ph']
    start_urls = ['http://tempo.com.ph/']
    website_id = 197  # 网站的id(必填)
    language_id = 1866  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(TempoSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = bs(response.text, 'html.parser')
        for i in soup.select('li.current-cat ~ li  a'):
            url = i.get('href')
            yield scrapy.Request(url, callback=self.parse_menu)

    def parse_menu(self, response):
        soup = bs(response.text, 'html.parser')
        allPages = soup.select_one('div.numbered-pagination > span').text.split()[-1] if soup.select_one('div.numbered-pagination > span').text else '0'  # 翻页
        for i in range(int(allPages)):
            url = response.url + 'page/' + str(i + 1) + '/'
            yield scrapy.Request(url, callback=self.parse_essay)

    def parse_essay(self, response):
        soup = bs(response.text, 'html.parser')
        for i in soup.select('#container > div')[1:-2]:  # 每页的文章
            url = i.select_one('a').get('href')
            pub_time = i.select_one('.entryDate').text if i.select_one('.entryDate').text else i.select_one('.meta_date').text
            if self.time == None or Util.format_time3(Util.format_time2(pub_time)) >= int(self.time):
                yield scrapy.Request(url, callback=self.parse_item)
            else:
                self.logger.info('时间截止')

    def parse_item(self, response):
        soup = bs(response.text, 'html.parser')
        item = DemoItem()
        category = soup.select('#bcrum > a')
        item['category1'] = category[1].text
        item['category2'] = category[2].text if category[2].text else None
        item['title'] = soup.select_one('h1.entry_title').text
        item['pub_time'] = Util.format_time2(soup.select_one('span.postDate').text)
        item['images'] = [i.get('src') for i in soup.select('#bcrum ~div >p >a>img')]
        item['abstract'] = soup.select_one('h1.entry_title').text
        ss = ''
        for i in soup.select('#bcrum ~div > p'):
            ss += i.text + r'\n'
        for i in soup.select('#bcrum ~ div >ol'):
            ss += i.text + r'\n'
        item['body'] = ss
        return item
