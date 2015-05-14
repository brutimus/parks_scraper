# -*- coding: utf-8 -*-
import datetime
from dateutil.parser import parse as du_parse
import scrapy
from scrapy.http import Request
import time
import urlparse

from parks_scraper.items import ParkHours


class DisneylandHoursSpider(scrapy.Spider):
    name = "disneyland_hours"
    allowed_domains = ["disneyland.disney.go.com"]
    start_urls = (
        'https://disneyland.disney.go.com/accessible-calendar/',
    )

    def parse_time(self, string):
        return datetime.time(*time.strptime(string.strip() + 'm', '%I:%M%p')[3:4])

    def parse_month(self, response):
        for day in response.css('#monthlyCalendar td'):
            # self.log(str(day))
            datelink = day.css('.dayOfMonth').xpath('a/@href')
            if not datelink:
                # Day of month is empty, skip
                continue
            date = du_parse(datelink.extract()[0].split('/')[-1])
            # self.log(str(date))
            for park in day.css('.cellSection'):
                open_time, close_time = park.css('.parkHours').xpath('text()').extract()[0].split('(')[0].split('-')
                yield ParkHours(
                    park=park.css('.parkName').xpath('text()').extract()[0],
                    date=date,
                    open_time=self.parse_time(open_time),
                    close_time=self.parse_time(close_time))

    def parse(self, response):
        yield Request(
            urlparse.urljoin(response.url, response.css('.nextDateNavSprite').xpath('@href').extract()[0]),
            callback=self.parse_month)
        for x in self.parse_month(response):
            yield x
