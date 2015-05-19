# -*- coding: utf-8 -*-
import datetime
from dateutil.parser import parse as du_parse
import scrapy
from scrapy.http import Request
import time
import urlparse

from parks_scraper.items import ParkHours, ParkPass


class DisneylandHoursSpider(scrapy.Spider):
    name = "disneyland_hours"
    allowed_domains = ["disneyland.disney.go.com"]
    start_urls = (
        'https://disneyland.disney.go.com/accessible-calendar/',
    )

    def parse_time(self, string):
        return datetime.time(
            *time.strptime(string.strip() + 'm', '%I:%M%p')[3:4])

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
                open_time, close_time = park.css('.parkHours').xpath('text()'
                    ).extract()[0].split('(')[0].split('-')
                yield ParkHours(
                    park=park.css('.parkName').xpath('text()').extract()[0],
                    date=date,
                    open_time=self.parse_time(open_time),
                    close_time=self.parse_time(close_time))

    def parse(self, response):
        yield Request(
            urlparse.urljoin(
                response.url,
                response.css('.nextDateNavSprite').xpath('@href').extract()[0]),
            callback=self.parse_month)
        for x in self.parse_month(response):
            yield x


class DisneylandPassesSpider(scrapy.Spider):
    name = "disneyland_passes"
    allowed_domains = ["disneyland.disney.go.com"]
    start_urls = (
        "https://disneyland.disney.go.com/passes/blockout-dates/",
    )
    pass_keys = {
        'dlr-premium-annual-pass': 'premium',
        'dlr-deluxe-annual-pass': 'deluxe',
        'dlr-socal-annual-pass': 'socal',
        'dlr-socal-select-annual-pass': 'socal_select'
    }

    def parse(self, response):
        pass_data = {}
        month = 0
        for pass_section in response.xpath(
                '//ul[@id="accordion"]/li[@data-type-pass]'):
            pass_key = pass_section.xpath(
                '@data-type-pass').extract()[0].strip()
            pass_name = pass_section.css('.passType').xpath(
                'text()').extract()[0].strip()
            self.log('Scraping pass: %s' % pass_name)
            year = datetime.date.today().year
            for month_calendar in pass_section.css('.calendar'):
                new_month = int(month_calendar.xpath(
                    '@data-month').extract()[0].strip())
                if new_month < month:
                    year += 1
                month = new_month
                self.log('Scraping month: %s/%s' % (new_month, year))
                for day_td in month_calendar.css('td:not(.noday)'):
                    day = int(day_td.xpath(
                        'span[not(@class)]/text()').extract()[0].strip())
                    boolean_text = day_td.xpath(
                        'span[@class="accessibleText"]/text()'
                        ).extract()[0].strip()
                    blocked = False if "Block" in boolean_text else True
                    key = (year, month, day)
                    date_data = pass_data.get(key, {})
                    date_data[self.pass_keys[pass_key]] = blocked
                    pass_data[key] = date_data
        for day, data in pass_data.items():
            dt = datetime.date(*day)
            yield ParkPass(date=dt, **data)
