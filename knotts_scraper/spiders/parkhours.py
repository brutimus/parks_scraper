# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
from dateutil.parser import parse as du_parse

from knotts_scraper.items import ParkHours


class ParkhoursSpider(scrapy.Spider):
    name = "parkhours"
    allowed_domains = ["knotts.com"]
    start_urls = (
        'https://www.knotts.com/hours-directions/park-hours',
    )

    def parse_hours(self, string):
        pass


    def parse(self, response):
        for month in response.css('.calendar'):
            self.log('Scraping: %s' % month.xpath('div[contains(@class, "month")]/text()').extract()[0])
            for day in month.xpath('div[contains(@class, "day") and @original-title]/@original-title').extract():
                sel = Selector(text='<div>%s</div>' % day)
                date_string = sel.xpath('//div/strong/text()').extract()[0]
                self.log('Parsed date: %s' % date_string)
                time_range_selection = sel.xpath('//div/text()').extract()
                if not time_range_selection:
                    continue
                self.log('Time range: %s' % time_range_selection[0])
                start, end = time_range_selection[0].split('-')
                start_date = du_parse('%s %s' % (date_string, start))
                end_date = du_parse('%s %s' % (date_string, end))
                yield ParkHours(
                    date=start_date.date(),
                    open_time=start_date.time(),
                    close_time=end_date.time())