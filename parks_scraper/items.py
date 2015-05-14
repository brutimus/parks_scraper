# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ShowtimeItem(scrapy.Item):
	name = scrapy.Field()
	date = scrapy.Field()
	times = scrapy.Field()
	location = scrapy.Field()


class ParkHours(scrapy.Item):
	park = scrapy.Field()
	date = scrapy.Field()
	open_time = scrapy.Field()
	close_time = scrapy.Field()