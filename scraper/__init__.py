import requests
import random
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SERIES_LIST_URL = "http://core.espnuk.org/v2/sports/cricket/leagues"
MATCH_REPORT_URL = "https://hs-consumer-api.espncricinfo.com/v1/pages/match/report"
MATCH_DETAIL_URL = "https://hs-consumer-api.espncricinfo.com/v1/pages/match/details"
COMMENTARY_URL = "https://hs-consumer-api.espncricinfo.com/v1/pages/match/comments"

TEST = 1
ODI = 2
T20I = 3


spoof_headers_raw = [{
				"name": "Accept",
				"value": "*/*"
			},
			{
				"name": "Accept-Encoding",
				"value": "gzip, deflate, br"
			},
			{
				"name": "Accept-Language",
				"value": "en-US,en;q=0.5"
			},
			{
				"name": "Host",
				"value": "hs-consumer-api.espncricinfo.com"
			},
			{
				"name": "Origin",
				"value": "https://www.espncricinfo.com"
			},
			{
				"name": "Referer",
				"value": "https://www.espncricinfo.com/"
			},
			{
				"name": "Sec-Fetch-Dest",
				"value": "empty"
			},
			{
				"name": "Sec-Fetch-Mode",
				"value": "cors"
			},
			{
				"name": "Sec-Fetch-Site",
				"value": "same-site"
			},
			{
				"name": "TE",
				"value": "trailers"
			},
			{
				"name": "User-Agent",
				"value": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0"
			}]

spoof_headers = {list(raw.values())[0]: list(raw.values())[1] for raw in spoof_headers_raw}

core_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Host": "core.espnuk.org",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0",
}


def json_resp(url, params=None, headers=None, debug=False):
  resp = requests.get(url, params=params, headers=headers)
  if debug:
    print(resp.request.url)

  try:
    return resp.json()
  except json.JSONDecodeError:
    return resp.text

def extract_items(data):
  return [x["$ref"] for x in data["items"]] 

def think_about_it_take_a_second(mean=0.2):
    sleep_for = abs(random.gauss(0, mean))
    time.sleep(sleep_for)

def scrape_and_save(fn, save_path, overwrite=False, *args, **kwargs):
    """run scraping fn and then save at given path"""

    if not overwrite and save_path.exists():
        return

    try:
        data = fn(*args, **kwargs)
        if isinstance(data, dict) and data.get("status"):
            if kwargs.get("debug"):
                print("Request error: {}, not saving {}".format(data.get("status", "unknown"), save_path))

            return
        elif not data:
            print("Data is empty, not saving args {}".format(save_path))
        else:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print("Saved data {}".format(save_path))
    except:
        print("Could not save data {} to {}".format(data, save_path))

def scrape_game(series_id, match_id, debug=False):
    def scrape_chunk(series_id, match_id, inning_num, from_over, debug=False):
        """
        scrapes a chunk of commentary via AJAX request. The commentary comes in json chunks of up to two overs
        """
        params = dict(
            lang="en", 
            seriesId=series_id, 
            matchId=match_id, 
            inningNumber=inning_num, 
            sortDirection="ASC", 
            commentType="ALL", 
            fromInningOver=from_over,
            )
        
        # think_about_it_take_a_second()

        return json_resp(COMMENTARY_URL, params, headers=spoof_headers, debug=False)
    
    if debug:
        print("Getting commentary for series {} match {}".format(series_id, match_id))

    inning_num = 1
    comms = []
    more_innings = True

    if not scrape_chunk(series_id, match_id, 1, 0)["comments"]:
        if debug:
            print("Game {} has no commentary".format(match_id))
        more_innings = False

    while more_innings:
        from_over = 0
        comms.append([])
        if debug:
            print("Series: {} Match: {} innings: {}".format(series_id, match_id, inning_num))

        while from_over is not None:
            chunk = scrape_chunk(series_id, match_id, inning_num, from_over, debug=debug)
            comms[inning_num-1]+=chunk["comments"]
            from_over=chunk["nextInningOver"]

        inning_num += 1
        if not scrape_chunk(series_id, match_id, inning_num, from_over)["comments"]:
            more_innings=False
            
    return comms


def get_match_detail(series_id, match_id, debug=False):
    match_detail = json_resp(MATCH_DETAIL_URL, {"seriesId": series_id, "matchId": match_id}, debug=debug)
    return match_detail

def extract_ids(urls):
    return [url.split("/")[-1] for url in urls]

def get_series_ids(class_id):
    first_page = json_resp(SERIES_LIST_URL, dict(page=1, classId=class_id), debug=False)
    page_count = first_page["pageCount"]
    urls = [(SERIES_LIST_URL, {"page": p, "classId": class_id}) for p in range(1, page_count + 1)]

    res = []
    with ThreadPoolExecutor() as exec:
        futures = [exec.submit(json_resp, *url) for url in urls]
        for future in as_completed(futures):
            res += [url for url in extract_items(future.result())]
    
    return extract_ids(res)

def get_seasons_meta(series_id):
    seasons_urls = json_resp("/".join([SERIES_LIST_URL, str(series_id), "seasons"]))
    return [json_resp(url) for url in extract_items(seasons_urls)]

def get_series_meta(series_id):
    return json_resp("{}/{}".format(SERIES_LIST_URL, series_id))

def extract_ids(urls):
    return [url.split("/")[-1] for url in urls]

def get_series_ids(class_id):
    def make_params(page, class_id):
        if class_id is None:
            return dict(page=page)
        else:
            return dict(page=page, classId=class_id)
    
    first_page = json_resp(SERIES_LIST_URL, make_params(1, class_id), debug=False)
    page_count = first_page["pageCount"]
    urls = [(SERIES_LIST_URL, make_params(p, class_id)) for p in range(1, page_count + 1)]

    res = []
    with ThreadPoolExecutor() as exec:
        futures = [exec.submit(json_resp, *url) for url in urls]
        for future in as_completed(futures):
            res += [url for url in extract_items(future.result())]

    return extract_ids(res)