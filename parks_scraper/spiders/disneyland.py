# -*- coding: utf-8 -*-
import datetime
from dateutil.parser import parse as du_parse
import re
import scrapy
from scrapy.http import Request
import time
import urlparse

from parks_scraper.items import ParkHours, ParkPass, DisneyDay


park_name_lookup = {
    'Disneyland Park': 'disneyland',
    'Disney California Adventure Park': 'disney-california-adventure'
}


class DisneylandHoursSpider(scrapy.Spider):
    name = "disneyland-hours"
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
                    park=park_name_lookup[park.css('.parkName').xpath('text()').extract()[0]],
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
    name = "disneyland-passes"
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


class DisneylandEventsSpider(scrapy.Spider):
    name = 'disneyland-events'
    allowed_domains = ["disneyland.disney.go.com"]
    start_urls = (
        "https://disneyland.disney.go.com/calendars/day/%s/",
    )
    days_to_scrape = 30
    parks = (
        'disneyland',
        'disney-california-adventure',
        'downtown-disney-district')
    schedule_contenttypes = (
        ('parades', 'parades'),
        ('night_shows', 'nighttime-spectacular-firework'),
        ('events', 'event'),
        ('shows', 'shows'),
        ('park_atmosphere', 'park-atmosphere-entertainment'))

    def start_requests(self):
        for delta in range(self.days_to_scrape):
            dt = datetime.date.today() + datetime.timedelta(delta)
            yield Request(self.start_urls[0] % dt.strftime('%Y-%m-%d'), self.parse, meta={
                'splash': {
                    'args': {
                        'html': 1,
                        'wait': 5
                    },
                    'endpoint': 'render.html',  # optional; default is render.json
                    'slot_policy': 'scrapyjs.SlotPolicy.SINGLE_SLOT'
                }
            })

    def process_time(self, reference_date, time_string):
        dt = du_parse('%s %s' % (
            reference_date.strftime('%Y-%m-%d'),
            time_string.replace(u'\xa0', ' ').strip()))
        if datetime.time(0, 0) <= dt.time() <= datetime.time(5, 0):
            dt += datetime.timedelta(1)
        return dt

    def parse(self, response):
        self.log(str(response.meta['_splash_processed']['args']['url'])+ ' - ' + str(len(response.css('.parades'))))
        if len(response.css('.parades')) == 0:
            self.log('Page did not load properly, resending...')
            yield Request(
                response.meta['_splash_processed']['args']['url'],
                self.parse,
                dont_filter=True,
                meta={
                    'splash': response.meta['_splash_processed']
                })
        else:
            date = du_parse(response.css('.date-second').xpath(
                'text()').extract()[0])

            for park in self.parks:
                park_div = response.css('#%s' % park)
                
                open_time, close_time = map(
                    lambda x:self.process_time(date, x), park_div.css(
                    '.parkHours').xpath( 'p/text()')[1].extract().split('to'))
                schedule_content = {}
                for content_type, content_class in self.schedule_contenttypes:
                    content_type_buffer = []
                    for content_element in park_div.css('.eventDetail.%s' % content_class):
                        if content_element.css('.scheduleUnavailableMessage'):
                            continue
                        name = content_element.css('.eventText').xpath(
                            'text()').extract()[0].strip()
                        time_string = content_element.css(
                            '.operatingHoursContainer').xpath(
                            'text()').extract()[0]
                        if 'to' in time_string:
                            times = self.process_time(
                                date,
                                time_string.split('to')[0].strip())
                        else:
                            times = map(
                                lambda x:self.process_time(date, x),
                                time_string.split(','))
                        content_type_buffer.append((name, times))
                    schedule_content[content_type] = content_type_buffer

                yield DisneyDay(
                    park=park,
                    date=date,
                    open_time=open_time,
                    close_time=close_time,
                    **schedule_content)


