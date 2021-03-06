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

class ParkPass(scrapy.Item):
	date = scrapy.Field()
	premium = scrapy.Field()
	deluxe = scrapy.Field()
	socal = scrapy.Field()
	socal_select = scrapy.Field()

class DisneyDay(scrapy.Item):
	date = scrapy.Field()
	park = scrapy.Field()
	open_time = scrapy.Field()
	close_time = scrapy.Field()
	parades = scrapy.Field()
	night_shows = scrapy.Field()
	events = scrapy.Field()
	shows = scrapy.Field()
	park_atmosphere = scrapy.Field()
	closures = scrapy.Field()
