# -*- coding: utf-8 -*-

# Scrapy settings for knotts_scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'knotts_scraper'

SPIDER_MODULES = ['knotts_scraper.spiders']
NEWSPIDER_MODULE = 'knotts_scraper.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'knotts_scraper (+http://www.yourdomain.com)'

FEED_URI = 's3://dev.seanstoops.com/knotts/%(name)s.pickle'