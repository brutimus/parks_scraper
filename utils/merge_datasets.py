# -*- coding: utf-8 -*-
import json
import petl


def main():
    park_hours = petl.fromjson('../data/parkhours.json')
    show_times = petl.fromjson('../data/showtimes.json')
    knotts_spreadsheet = petl.fromcsv(
        'https://spreadsheets.google.com/tq?key=1_wmXgh1zuljwzH2O1eW_BTBkxDkxyckLzSD9cT4Kn2Q&gid=0&tqx=out:csv'
        )

    spreadsheet_lookup = {}
    for item in knotts_spreadsheet.dicts():
        spreadsheet_lookup[item['date']] = {
            'crowd_level': item['crowd_level'],
            'closures': map(unicode.strip, item['closures'].split(','))
        }

    show_times_lookup = {}
    for item in show_times.dicts():
        show_times_lookup[item['date']] = show_times_lookup.get(
            item['date'], []) + [{'times': item['times'], 'location': item['location']}]

    new_park_hours = []
    for day in park_hours.dicts():
        st = show_times_lookup.get(day['date'])
        if st:
            day['show_times'] = st
        sheet_item = spreadsheet_lookup.get(day['date'])
        if sheet_item:
            day.update(sheet_item)
        new_park_hours.append(day)
    with open('../data/merged_data.json', 'w+') as f:
        json.dump(new_park_hours, f)


if __name__ == '__main__':
    main()