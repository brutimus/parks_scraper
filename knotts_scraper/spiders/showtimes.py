# -*- coding: utf-8 -*-
import datetime
import itertools
import re
import scrapy
from daterangeparser import parse as dr_parse
from dateutil.parser import parse as du_parse

from knotts_scraper.items import ShowtimeItem


DOW = (
    'Sun',
    'Mon',
    'Tue',
    'Wed',
    'Thurs',
    'Fri',
    'Sat'
)


class ShowtimesSpider(scrapy.Spider):
    name = "showtimes"
    allowed_domains = ["knotts.com"]
    start_urls = (
        'http://www.knotts.com/plan-a-visit/show-times',
    )


    def process_date_choices(self, string):
        self.log('Processing date choices: %s' % string)
        dates = [None] * 7
        start_date, end_date = dr_parse(string)
        self.log(str(start_date) + ' - ' + str(end_date))
        index = start_date.date()
        while index <= end_date.date():
            self.log(str(index) + ', ' + str(index.isoweekday() % 7))
            dates[index.isoweekday() % 7] = index
            index += datetime.timedelta(1)
        return dates


    def process_dates(self, string, date_choices):
        self.log('Processing dates: %s' % string)
        string = string.replace('nesday', '')
        string = string.replace('urday', '')
        string = string.replace('day', '')
        string = string.replace('.', '')
        self.log('Cleaned date string: %s' % string)
        for index, day in enumerate(DOW):
            string = string.replace(day, str(index))
        self.log('Subbed date string: %s' % string)
        
        dates = []

        for segment in re.split('[,;&]', string):
            segment = segment.strip()
            if len(segment) == 1:
                index = int(segment)
                dates.append(date_choices[index])
            elif segment.find('-') >= 0:
                for x in range(int(segment[0]), int(segment[-1]) + 1):
                    dates.append(date_choices[x])

        return dates


    def process_datetimes(self, string, date_choices):
        self.log('Processing datetimes: %s' % string)
        s = string.replace(u'–', u'-')
        if '(' in s:
            times, dates = re.findall(r'([\w,:;&. ]+)\(([\w\-,& .]+)\)', s)[0]
            dates = self.process_dates(dates, date_choices)
        else:
            times = re.findall(r'([\w,:;&. ]+)', s)[0]
            dates = [x for x in date_choices if x is not None]
        self.log('Processed dates: %s' % dates)
        times = re.split('[,;&]', times)
        times = [(x.strip().endswith('m.') or x.strip().endswith('m'))
            and x.strip() or (x.strip() + ' p.m.') for x in times]
        times = map(lambda x:du_parse(x).time(), times)
        self.log('Processed times: %s' % times)
        datetimes = map(lambda x:datetime.datetime.combine(*x), itertools.product(dates, times))
        self.log(str(datetimes))
        return datetimes


    def parse(self, response):
        schedule = []
        for block in response.css('.listingitem.questions .text.wide'):
            date_choices = self.process_date_choices(
                block.css('.faq').xpath('text()').extract()[0].strip())
            for event_cell in block.css('table tbody tr td p'):
                name = event_cell.xpath('strong/text() | b/text()').extract()[0].strip().title()
                self.log(name)
                location_cache = None
                # Reverse so we can cache the location first
                for line_item in reversed(event_cell.xpath('text()').extract()):
                    line_item = line_item.strip()
                    if re.match(r'^\d.+', line_item):
                        datetimes = self.process_datetimes(line_item, date_choices)
                        for dt in datetimes:
                            yield ShowtimeItem(name=name, datetime=dt, location=location_cache)
                    elif line_item.startswith('Loc'):
                        line_item = line_item.replace('Location:', '').strip()
                        location_cache = line_item
            

