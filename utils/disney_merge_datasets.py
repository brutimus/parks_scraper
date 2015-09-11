# -*- coding: utf-8 -*-
from dateutil.parser import parse as du_parse
import boto
import forecastio
import os
import pickle
import petl
import requests
import tinys3
import shutil
from StringIO import StringIO


# The following fixes a bug where boto fails to load buckets with dots
# https://github.com/boto/boto/issues/2836#issuecomment-68682573

import ssl

if hasattr(ssl, 'match_hostname'):
  _old_match_hostname = ssl.match_hostname

  def _new_match_hostname(cert, hostname):
     if hostname.endswith('.s3.amazonaws.com'):
        pos = hostname.find('.s3.amazonaws.com')
        hostname = hostname[:pos].replace('.', '') + hostname[pos:]
     return _old_match_hostname(cert, hostname)

  ssl.match_hostname = _new_match_hostname


FORECAST_IO_API_KEY = os.environ.get('FORECAST_IO_API_KEY')
DISNEY_SPREADSHEET_KEY = os.environ.get('DISNEY_SPREADSHEET_KEY')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_CDN = os.environ.get('S3_CDN')


DISNEY_LAT = 33.811152
DISNEY_LNG = -117.921971


def get_forecast():
    forecast = forecastio.load_forecast(
        FORECAST_IO_API_KEY, DISNEY_LAT, DISNEY_LNG)
    return {x.time.replace(hour=0, minute=0, second=0, microsecond=0):
        x.d for x in forecast.daily().data}
        

def s3_save(f, filename):
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(S3_BUCKET)
    key = bucket.new_key('parks/%s' % filename)
    f.seek(0)
    key.set_contents_from_file(f)
    f.seek(0)

def s3_open(filename):
    r = requests.get('http://%s/parks/%s' % (S3_BUCKET, filename))
    return StringIO(r.content)


def load_pickles(filename):
    buff = []
    f = s3_open(filename)
    while True:
        try:
            buff.append(pickle.load(f))
        except EOFError, e:
            break
    return buff


def main():
    hours = load_pickles('disneyland-hours.pickle')
    events = load_pickles('disneyland-events.pickle')
    passes = load_pickles('disneyland-passes.pickle')
    forecast = get_forecast()
    spreadsheet = petl.fromcsv(
        'https://spreadsheets.google.com/tq?key=%s&gid=0&tqx=out:csv' % 
            DISNEY_SPREADSHEET_KEY
    )

    events_lookup = {}
    for item in events:
        buff = events_lookup.get(item['date'].date(), {})
        buff[item['park']] = item
        buff['date'] = item['date'].date()
        events_lookup[item['date'].date()] = buff

    for item in spreadsheet.dicts():
        # print item
        sheet_date = du_parse(item['date']).date()
        if events_lookup.has_key(sheet_date):
            e = events_lookup[sheet_date]
            e['disneyland']['crowd_level'] = item['disneyland_crowd_level']
            e['disneyland']['closures'] = [x for x in map(
                unicode.strip,
                item['disneyland_closures'].split(',')) if x]
            e['disney-california-adventure']['crowd_level'] = \
                item['california_adventure_crowd_level']
            e['disney-california-adventure']['closures'] = \
                [x for x in map(
                    unicode.strip,
                    item['california_adventure_closures'].split(',')) if x]

    for item in hours:
        if events_lookup.has_key(item['date'].date()):
            events_lookup[item['date'].date()][item['park']]['hours'] = item

    for item in passes:
        # print item
        if events_lookup.has_key(item['date']):
            events_lookup[item['date']]['passes'] = item

    for date, item in forecast.items():
        if events_lookup.has_key(date.date()):
            events_lookup[date.date()]['forecast'] = item

    f = StringIO()
    from pprint import pprint
    pprint(events_lookup)
    pickle.dump(sorted(events_lookup.values(), key=lambda x:x['date']), f)
    s3_save(f, 'disneyland-merged_data.pickle')
    f.seek(0)
    s3_save(f, 'disney-california-adventure-merged_data.pickle')


if __name__ == '__main__':
    main()