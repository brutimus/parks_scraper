# Knott's Berry Farm Scraper

This is a Python Scrapy project to build a daily schedule for Knott's Berry Farm.

## Data sources

 - [Park Hours](https://www.knotts.com/hours-directions/park-hours)
 - [Events Schedule](https://www.knotts.com/plan-a-visit/show-times)
 - [Ride Closures](https://www.knotts.com/hours-directions/park-hours) (left rail)
 - [Forecast](http://forecast.io)
 - This also pulls some additional data from a proprietary Google Spreadsheet
 
## Usage
    pip install -r requirements.txt
    mkdir data
    scrapy crawl showtimes -o data/showtimes.json
    scrapy crawl parkhours -o data/parkhours.json
    cd utils/
    python merge_datasets.py

Note: Add FORECAST_IO_API_KEY and KNOTTS_SPREADSHEET_KEY to private.py before running the merge_datasets.py script