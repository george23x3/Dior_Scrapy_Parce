import scrapy
import json
import re
import datetime


class DiorSpider(scrapy.Spider):
    name = 'dior'
    start_urls = [
        'https://www.dior.com/en_us/', 'https://www.dior.com/fr_fr'
    ]

    def parse(self, response):
        for href in response.css(".navigation-item-link::attr(href)"):
            yield response.follow(href, self.parse_products)

    def parse_products(self, response):
        for href in response.css('.product-link::attr(href)'):
            yield response.follow(href, self.parse_stuff)

    def parse_stuff(self, response):
        scan = json.loads(re.findall(r'(window.initialState \= )(.+?)(\n)',
                                     response.css("script::text").getall()[5],
                                     re.MULTILINE)[0][1])
        scan_for_av = json.loads(re.findall(r"(var dataLayer \= \[)(.*?)(\]\;\n)",
                                            response.css("script::text").getall()[2],
                                            re.MULTILINE)[0][1])
        data = scan['CONTENT']['contents'][0]['cmsContent']['elements'][5]
        if data['type'] == "PRODUCTVARIATIONS":
            if data["variationsType"] == "SIZE":
                flag = 'size'
            elif data["variationsType"] == "CAPACITY":
                flag = 'cap'
            else:
                flag = 'swatch'                         # SWATCH

            data1 = data['variations']
            for item in data1:
                if flag == 'size':
                    availability = True if item['status'] == 'AVAILABLE' else False
                    color = item['tracking'][0]['ecommerce']['add']["products"][0]["variant"]
                    size = item['title']
                elif flag == 'cap':
                    availability =\
                        True if scan_for_av['ecommerce']['detail']['products'][0]['dimension25'] == "inStock" else False
                    size = item['tracking'][0]['ecommerce']['add']["products"][0]["variant"]
                    color = ''
                elif flag == 'swatch':
                    availability = \
                        True if scan_for_av['ecommerce']['detail']['products'][0]['dimension25'] == "inStock" else False
                    size = ''
                    color = item['title']
                yield {
                    'name':
                        item['tracking'][0]['ecommerce']['add']["products"][0]["name"].replace("\\", ''),
                    'value': item['price']['value'],
                    'currency': item['price']['currency'],
                    'category': item['tracking'][0]['ecommerce']['add']["products"][0]["category"],
                    'sku': item['sku'],
                    'availability': availability,
                    'timeOfScan':
                        datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
                    'color': color,
                    'size': size,
                    'region': response.url[24:26],
                    'description':
                        response.css('meta[name="description"]::attr(content)').get().split('  ')[0].replace('\n', ' ')
                    }
        else:
            yield {
                'name':
                    data['tracking'][0]['ecommerce']['add']["products"][0]["name"].replace("\\", ''),
                'value': data['price']['value'],
                'currency': data['price']['currency'],
                'category': data['tracking'][0]['ecommerce']['add']["products"][0]["category"],
                'sku': data['sku'],
                'availability':
                    True if scan_for_av['ecommerce']['detail']['products'][0]['dimension25'] == "inStock" else False,
                'timeOfScan':
                    datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
                'color': '',
                'size': '',
                'region': response.url[24:26],
                'description':
                    response.css('meta[name="description"]::attr(content)').get().split('  ')[0].replace('\n', ' ')
            }
