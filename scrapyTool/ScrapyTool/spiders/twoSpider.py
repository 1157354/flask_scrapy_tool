import scrapy
import pymysql
from app.setting import *
from scrapy import Request
# from app.views import getScrapyList
# from app.views import getWebsite
# from app.views import getCurType
# from app.views import getpagenum
from scrapyTool.ScrapyTool.items import MyItem
import logging,redis
from app.User import UserInfo


class conSpider(scrapy.Spider):
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 600,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
            'scrapyTool.ScrapyTool.middlewares.MyUserAgentMiddleware': 400,
            'scrapyTool.ScrapyTool.middlewares.SeleniumMiddleware': 543,
        },
        "ITEM_PIPELINES": {
            'ScrapyTool.pipelines.RedisPipeline': 200,
            'ScrapyTool.pipelines.TestPipeline': 300,
        }
    }

    name = "content"

    def __init__(self, id='', **kwargs):
        super(conSpider, self).__init__(**kwargs)
        self.conn = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT)
        self.cursor = self.conn.cursor()
        self.aid = id
        print("aid:", self.aid)
        self.r = redis.StrictRedis(host=RHOST, port=RPORT)
        self.userinfo = UserInfo.from_json(self.r.get(self.aid))
    #     self.bloom = BloomFilter(max_elements=100000, error_rate=0.05)
    #     self._getWebsitesInDB()
    #
    # def _getWebsitesInDB(self):
    #     table_name = getCurType()
    #     sql = 'select 网址 from %s' % table_name
    #     self.cursor.execute(sql)
    #     results = self.cursor.fetchall()
    #     print(results)
    #     if results is not None:
    #         for r in results:
    #             self.bloom.add(r[0])

    def start_requests(self):
        website = self.userinfo['website']
        print("website:", website)
        num = int(website['pagenum']) + 1
        for page in range(1, num):
            yield Request(url=website, callback=self.parse, dont_filter=True, meta={'page': page})

    def parse(self, response):
        print("---start 2 selenium---")
        item = MyItem()
        dicta = {}
        xpathList = []
        combination = []
        scrapyList = self.userinfo['fields_xpath_list']
        # out_list = getlistxpath()
        # out_list = "//*[@id='searchForm']/div/div[2]/table/tbody//tr/td[1]/a/text()"
        # all = response.xpath(scrapyList).extract()
        # print("all:", all)
        table_name = self.userinfo['table_name']
        sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(table_name)
        cursor = self.conn.cursor()
        cursor.execute(sql_order)
        result = cursor.fetchall()
        print("result:", result)
        for r in result:
            xpathList.append(r[0])  # 字段名
        for i in zip(scrapyList, xpathList):
            if i[0] and i[1]:
                combination.append(i)  # xpath 对应 字段名
        for c in combination:
            dicta[c[1]] = response.xpath(c[0]).extract()
        logging.info("dicta: {}".format(dicta))
        item = dicta
        yield item
