# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from scrapy.selector import Selector

HEADERS = {
           'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
           'Host': 'www.crateandbarrel.com',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'Connection': 'keep-alive',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
           }
        #    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
        #       "Chrome/63.0.3239.84 Safari/537.36"

class CrateAndBarrelSpider(scrapy.Spider):
    name = "crate-and-barrel"
    allowed_domains = ["crateandbarrel.com"]
    download_delay = 5
    
    # start_urls = (
    #     'https://www.crateandbarrel.com/stores/list-state/retail-stores',
    # )
    # tried METAREFRESH_ENABLED = False in settings but doesn't work, if not redirect, there's 200 but no pages crawled

    def start_requests(self):
        start_urls = 'https://www.crateandbarrel.com/stores/list-state/retail-stores'
        meta={
            'dont_redirect': True,
            # 'handle_httpstatus_list': [302, 503]
        }
        # download_delay = 0.1

        yield scrapy.Request(url=start_urls, headers=HEADERS, callback=self.parse) # dont_filter=True, meta=meta,

    def parse(self, response):
        state_urls = response.xpath('//div[@class="state-list"]/ul/li/a').xpath("@href").extract()
        for state_url in state_urls:
            url = 'https://www.crateandbarrel.com' + state_url
            print('path: ', state_url)
            yield scrapy.Request(
                url=url,
                headers=HEADERS,
                # meta={
                #     'dont_redirect': True,
                #     'handle_httpstatus_list': [302],
                #     'dont_filter': True,
                # },
                callback=self.parse_stores,
            )
    
    def parse_stores(self, response):
        pois = response.xpath('//script[@type="application/ld+json" and contains(text(), "geo")]/text()').extract()
        for poi in pois:
            basic_info = json.loads(poi)
            name = basic_info['name']
            store_page = response.xpath('//div[contains(@class, "store-list")]/div/div/a/h2[contains(text(), "{name}")]/@data-href'.format(name=name)).get()

            properties = {
                'ref': store_page.split('/')[-1],
                'website': 'https://www.crateandbarrel.com' + store_page,
                'name': basic_info['name'],
                'addr_full': basic_info['address']['streetAddress'],
                'city': basic_info['address']['addressLocality'],
                'state': basic_info['address']['addressRegion'],
                'postcode': basic_info['address']['postalCode'],
                'country': basic_info['address']['addressCountry'],
                'phone': basic_info['telephone'],
                'opening_hours': basic_info['openingHours'],
                'lat': basic_info['geo']['latitude'],
                'lon': basic_info['geo']['longitude'],
            }

            yield GeojsonPointItem(**properties)
