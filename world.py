import scrapy
from demo.util import Util
from demo.items import DemoItem
from bs4 import BeautifulSoup as bs
from scrapy.http import Request, Response
import re
import time
import requests


class WorldSpider(scrapy.Spider):
    name = 'world'
    allowed_domains = ['worldnews.net.ph']
    start_urls = ['https://worldnews.net.ph/']
    website_id = 183  # 网站的id(必填)
    language_id = 2266  # 所用语言的id
    sql = {  # my sql 配置
        'host': '192.168.235.162',
        'user': 'dg_ldx',
        'password': 'dg_ldx',
        'db': 'dg_test'
    }

    def __init__(self, time=None, *args, **kwargs):
        super(WorldSpider, self).__init__(*args, **kwargs)  # 将这行的DemoSpider改成本类的名称
        self.time = time

    def parse(self, response):
        soup = bs(response.text, 'html.parser')
        m = {}
        for i in soup.select('#menu-main-menu>li> a')[1:-1]:
            url = i.get('href')
            m['category1'] = i.get('title')
            yield scrapy.Request(url, callback=self.parse_menu, meta=m)

    def parse_menu(self, response):
        soup = bs(response.text, 'html.parser')
        for i in soup.select('article > div.content '):  # 每页的文章
            url = i.select_one('a').get('href')
            if self.time == None or Util.format_time3(i.select_one('time').text+' 00:00:00') >= int(self.time):
                yield scrapy.Request(url, meta=response.meta, callback=self.parse_item)
            else:
                self.logger.info('时间截止')

        try:
            allPages = soup.select('ul.pagination > li')[-2].text if soup.select('ul.pagination > li')[
                -2].text else None  # 翻页
            if allPages:
                for i in range(int(allPages)):
                    url = response.url + '/?page=' + str(i + 1)
                    yield scrapy.Request(url, meta=response.meta, callback=self.parse_menu)
        except:
            self.logger.info(response.url)
            self.logger.info('Next page no more !')

    # def parse_essay(self, response):
    #     soup = bs(response.text, 'html.parser')
    #     for i in soup.select('article > div.content a'):  # 每页的文章
    #         url = i.get('href')
    #         yield scrapy.Request(url, meta=response.meta, callback=self.parse_item)

    def parse_item(self, response):
        soup = bs(response.text, 'html.parser')
        item = DemoItem()
        item['category1'] = response.meta['category1']
        item['category2'] = None
        item['title'] = soup.select_one('#rg-gallery h1').text
        item['pub_time'] = soup.select('time.value-title')[0].text + ' 00:00:00'
        item['images'] = None
        item['abstract'] = soup.select('article > div > div >div >p')[0].text
        ss = ''
        for i in soup.select('article > div > div >div >p'):
            ss += i.text + r'\n'
        item['body'] = ss
        return item
