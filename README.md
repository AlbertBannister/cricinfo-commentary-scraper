# cricinfo-commentary-scraper

Utility for scraping series, match, and ball-by-ball data from popular Cricket news site ESPNCricinfo. For whatever reason they have some very convenient exposed APIs which return lovely JSON data

## Set up venv

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Importing
Since it isn't packaged properly yet, we add the project base directory to our path,
in this case relative to /notebooks

    import sys
    sys.append("..")
    import scraper

## Notebooks
Look ahead for notes on the API, or run the notebooks in the order given. The notebooks are meant to be run for one format at a time to reduce 

### 1.
**get_series.ipynb** walks through and gets all series corresponding to your given format of interest, and saves the series and season metadata in a year/series-slug/metadata.json structure

### 2.
**get_matches.ipynb** walks through the save series metadata and gets all events associated with each season (occurence of a series)

### 3.
**get_commentary.ipynb** walks through saved event metadata and attempts to scrape the ball by ball metadata, if it exists.

# The API
PROPER DOCUMENTATION COMING SOON
This is not complete documentation of the API(s) but a brief overview. 

The main database entities are "series" which can be either a repeating tournament (e.g. ODI world cup) or a one off between two teams, "seasons" which appear to be a particular instantiation of a series (e.g. the 2019 ODI world cup), and "events" which are effectively games. There appears to be support for multiple games within a single "event" though I haven't come across this used yet.

If we have the series_id and match_id, we can retrieve anything about the game. There are some mappings with series_id which we're figuring out.

We make use of two APIs - core.espnuk.org/v2/sports/cricket/ which offers paginated outputs for getting series and matches easily. I suspect it's deprecated as it doesn't appear to be used anywhere when I inspect pages

https://hs-consumer-api.espncricinfo.com/v1/pages/match/scorecard provides all the metadata about a match

https://hs-consumer-api.espncricinfo.com/v1/pages/match/comments provides all the ball-by-ball commentary for a match



