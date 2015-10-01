# Amusement Parks Scraper
This is a Python Scrapy project to retrieve schedule and show information
for amusement parks.

## Supported parks
 - Knott's Berry Farm
 - Disneyland

## Data sources
- [Forecast](http://forecast.io)

### Knott's Berry Farm
 - [Park Hours](https://www.knotts.com/hours-directions/park-hours)
 - [Events Schedule](https://www.knotts.com/plan-a-visit/show-times)
 - [Ride Closures](https://www.knotts.com/hours-directions/park-hours) (left rail)
 - This also pulls some additional data from a proprietary Google Spreadsheet

### Disney
- [Events](https://disneyland.disney.go.com/calendars/day/)
- [Hours](https://disneyland.disney.go.com/accessible-calendar/)
- [Passes](https://disneyland.disney.go.com/passes/blockout-dates/)
 
## Usage
The scrapy applications pull the data from the source and store it in an S3 bucket in the pickle format. The 'merger' scripts then download these data files and merge them together into the final output.

    pip install -r requirements.txt

### Knott's Berry Farm
    scrapy crawl knotts-showtimes
    scrapy crawl knotts-hours
    python utils/merge_datasets.py

### Disney
Due to the way the Disneyland website is dynamically rendered, the scraper requires a [Splash](https://github.com/scrapinghub/splash) instance be running. See below for documentation.

    *start Splash instance in a seperate terminal*
    scrapy crawl disneyland-events
    scrapy crawl disneyland-passes
    scrapy crawl disneyland-hours
    python utils/disney_merge_datasets.py

## Splash
>Lightweight, scriptable browser as a service with an HTTP API

Simply install Docker and Splash as per their [documentation](http://splash.readthedocs.org/en/stable/install.html).

    docker pull scrapinghub/splash
    docker run -p 5023:5023 -p 8050:8050 -p 8051:8051 scrapinghub/splash
    boot2docker ip (Use this IP to change the one in settings.py)

## Environment Variables
	export FORECAST_IO_API_KEY=''
	export KNOTTS_SPREADSHEET_KEY=''
	export AWS_ACCESS_KEY_ID=''
    export AWS_SECRET_ACCESS_KEY=''
	export S3_ACCESS_KEY=''
	export S3_SECRET_KEY=''
	export S3_BUCKET=''
	export S3_ENDPOINT=''