# -*- coding: utf-8 -*-
import forecastio
import json
import petl

from private import FORECAST_IO_API_KEY, KNOTTS_SPREADSHEET_KEY

KNOTTS_LAT = 33.844317
KNOTTS_LNG = -118.000227


def get_forecast():
    forecast = forecastio.load_forecast(
        FORECAST_IO_API_KEY, KNOTTS_LAT, KNOTTS_LNG)
    return {x.time.strftime('%Y-%m-%d'):x for x in forecast.daily().data}


def main():
    park_hours = petl.fromjson('../data/parkhours.json')
    show_times = petl.fromjson('../data/showtimes.json')
    knotts_spreadsheet = petl.fromcsv(
        'https://spreadsheets.google.com/tq?key=%s&gid=0&tqx=out:csv' % KNOTTS_SPREADSHEET_KEY
    )
    forecast = get_forecast()

    spreadsheet_lookup = {}
    for item in knotts_spreadsheet.dicts():
        spreadsheet_lookup[item['date']] = {
            'crowd_level': item['crowd_level'],
            'closures': map(unicode.strip, item['closures'].split(','))
        }

    show_times_lookup = {}
    for item in show_times.dicts():
        show_times_lookup[item['date']] = show_times_lookup.get(
            item['date'], []) + [{
                'name': item['name'],
                'times': item['times'], 
                'location': item['location']}]

    new_park_hours = []
    for day in park_hours.dicts():

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
    with open('../data/merged_data.json', 'w+') as f:
        json.dump(new_park_hours, f)


if __name__ == '__main__':
    main()