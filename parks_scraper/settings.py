# -*- coding: utf-8 -*-

# Scrapy settings for knotts_scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'parks_scraper'

SPIDER_MODULES = ['parks_scraper.spiders']
NEWSPIDER_MODULE = 'parks_scraper.spiders'

# CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 1

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.36'

FEED_URI = 's3://dev.seanstoops.com/parks/%(name)s.pickle'
FEED_FORMAT = 'pickle'
FEED_EXPORTERS_BASE = {
    'json': 'scrapy.contrib.exporter.JsonItemExporter',
    'jsonlines': 'scrapy.contrib.exporter.JsonLinesItemExporter',
    'csv': 'scrapy.contrib.exporter.CsvItemExporter',
    'xml': 'scrapy.contrib.exporter.XmlItemExporter',
    'marshal': 'scrapy.contrib.exporter.MarshalItemExporter',
    'pickle': 'scrapy.contrib.exporter.PickleItemExporter'
}

SPLASH_URL = 'http://192.168.59.103:8050'

DOWNLOADER_MIDDLEWARES = {
    'parks_scraper.scrapyjsmiddleware.SplashMiddleware': 725,
}

DUPEFILTER_CLASS = 'parks_scraper.scrapyjsdupefilter.SplashAwareDupeFilter'


# The following fixes a bug where boto fails to load buckets with dots
# https://github.com/boto/boto/issues/2836#issuecomment-68682573

import ssl

# _old_match_hostname = ssl.match_hostname

def _new_match_hostname(cert, hostname):
   if hostname.endswith('.s3.amazonaws.com'):
      pos = hostname.find('.s3.amazonaws.com')
      hostname = hostname[:pos].replace('.', '') + hostname[pos:]
   return _old_match_hostname(cert, hostname)

ssl.match_hostname = _new_match_hostname