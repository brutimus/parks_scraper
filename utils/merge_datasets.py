# -*- coding: utf-8 -*-
from dateutil.parser import parse as du_parse
import forecastio
import pickle
import petl
import tinys3
import shutil
from StringIO import StringIO

from private import (
    FORECAST_IO_API_KEY,
    KNOTTS_SPREADSHEET_KEY,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET,
    S3_ENDPOINT
)


KNOTTS_LAT = 33.844317
KNOTTS_LNG = -118.000227


def get_forecast():
    forecast = forecastio.load_forecast(
        FORECAST_IO_API_KEY, KNOTTS_LAT, KNOTTS_LNG)
    return {x.time.strftime('%Y-%m-%d'):x for x in forecast.daily().data}


def save(f, filename):
    conn = tinys3.Connection(
        S3_ACCESS_KEY,
        S3_SECRET_KEY,
        endpoint=S3_ENDPOINT)
    f.seek(0)
    conn.upload('knotts/%s' % filename, f, S3_BUCKET)
    f.seek(0)
    with open('../data/%s' % filename, 'w+') as fo:
        shutil.copyfileobj(f, fo)
    f.seek(0)


def load_pickles(filename):
    buff = []
    with open(filename, 'rb') as f:
        while True:
            try:
                buff.append(pickle.load(f))
            except EOFError, e:
                break
    return buff


def main():
    park_hours = load_pickles('../data/parkhours.pickle')
    show_times = load_pickles('../data/showtimes.pickle')
    knotts_spreadsheet = petl.fromcsv(
        'https://spreadsheets.google.com/tq?key=%s&gid=0&tqx=out:csv' % KNOTTS_SPREADSHEET_KEY
    )
    forecast = get_forecast()

    spreadsheet_lookup = {}
    for item in knotts_spreadsheet.dicts():
        spreadsheet_lookup[du_parse(item['date']).date()] = {
            'crowd_level': item['crowd_level'],
            'closures': map(unicode.strip, item['closures'].split(','))
        }

    show_times_lookup = {}
    for item in show_times:
        show_times_lookup[item['date']] = show_times_lookup.get(
            item['date'], []) + [{
                'name': item['name'],
                'times': item['times'], 
                'location': item['location']}]

    new_park_hours = []
    for day in park_hours:

        st = show_times_lookup.get(day['date'])
        if st:
            day['show_times'] = st

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
    save(f, 'merged_data.pickle')


if __name__ == '__main__':
    main()