# -*- coding: utf-8 -*-
from dateutil.parser import parse as du_parse
import forecastio
import os
import pickle
import petl
import requests
import tinys3
import shutil
from StringIO import StringIO


FORECAST_IO_API_KEY = os.environ.get('FORECAST_IO_API_KEY')
KNOTTS_SPREADSHEET_KEY = os.environ.get('KNOTTS_SPREADSHEET_KEY')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_CDN = os.environ.get('S3_CDN')


KNOTTS_LAT = 33.844317
KNOTTS_LNG = -118.000227


def get_forecast():
    forecast = forecastio.load_forecast(
        FORECAST_IO_API_KEY, KNOTTS_LAT, KNOTTS_LNG)
    return {x.time.date():x for x in forecast.daily().data}


def s3_save(f, filename):
    conn = tinys3.Connection(
        S3_ACCESS_KEY,
        S3_SECRET_KEY,
        endpoint=S3_ENDPOINT)
    f.seek(0)
    conn.upload('parks/knotts-%s' % filename, f, S3_BUCKET)
    f.seek(0)


def s3_open(filename):
    r = requests.get('http://%s/parks/%s' % (S3_CDN, filename))
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
    park_hours = load_pickles('knotts-hours.pickle')
    soak_city_hours = load_pickles('soakcity-hours.pickle')
    show_times = load_pickles('knotts-showtimes.pickle')
    knotts_spreadsheet = petl.fromcsv(
        'https://spreadsheets.google.com/tq?key=%s&gid=0&tqx=out:csv' % 
            KNOTTS_SPREADSHEET_KEY
    )
    forecast = get_forecast()

    spreadsheet_lookup = {}
    for item in knotts_spreadsheet.dicts():
        spreadsheet_lookup[du_parse(item['date']).date()] = {
            'crowd_level': item['crowd_level'],
            'closures': [
                x for x in map(unicode.strip, item['closures'].split(',')) if x]
        }

    # Condense the event listing to one listing per event ignoring location
    condensed_st = {}
    for item in show_times:
        key = (item['date'], item['name'])
        buff = condensed_st.get(key)
        if buff:
            buff['times'] = sorted(buff['times'] + item['times'])
        else:
            buff = item
        condensed_st[key] = buff


    show_times_lookup = {}
    for item in condensed_st.values():
        show_times_lookup[item['date']] = show_times_lookup.get(
            item['date'], []) + [{
                'name': item['name'],
                'times': item['times']}]
                # 'location': item['location']}] # We don't use loc, ignore

    soak_city_hours_lookup = {}
    for item in soak_city_hours:
        soak_city_hours_lookup[item['date']] = {
            'open_time': item.get('open_time'),
            'close_time': item.get('close_time')
        }

    new_park_hours = []
    for day in park_hours:

        st = show_times_lookup.get(day['date'])
        if st:
            day['show_times'] = sorted(st, key=lambda x:x['name'])

        ss = soak_city_hours_lookup.get(day['date'])
        if ss:
            day['soak_city_hours'] = ss

        sheet_item = spreadsheet_lookup.get(day['date'])
        if sheet_item:
            day.update(sheet_item)

        forecast_item = forecast.get(day['date'])
        if forecast_item:
            day['temperatureMax'] = forecast_item.temperatureMax
            day['temperatureMin'] = forecast_item.temperatureMin
            day['weatherIcon'] = forecast_item.icon
        new_park_hours.append(day)

    f = StringIO()
    pickle.dump(new_park_hours, f)
    s3_save(f, 'merged_data.pickle')


if __name__ == '__main__':
    main()