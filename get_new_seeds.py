import random
import string
import time

from random_word import RandomWords
from scrap_request import app_details
from cloud_db import app_exist
import play_scraper

from utils.lang_detect import is_english

r = RandomWords()


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def analyse_apps(app_ids: list):
    apps_ids_not_games = []
    for app_id in app_ids:
        details = app_details(app_id)
        if details['category'] and is_english(details):
            apps_ids_not_games.append(app_id)
        category = list(details['category'])
        if any("GAME" not in s for s in category) and is_english(details):
            apps_ids_not_games.append(app_id)
    return set(apps_ids_not_games)


def get_random_word():
    try:
        # sometimes this function call gives network error, get a random string instead
        return r.get_random_word()
    except:
        return get_random_string(5)


def get_new_seeds(num: int):
    # num must be at least one
    if num <= 0:
        num = 1
    # search 10000 words maximum
    ok_ids = set()
    for k in range(10000):
        word = get_random_word()
        # there are maximum 12 pages
        for i in range(13):
            app_ids = []
            apps_returned = play_scraper.search(word, page=i)
            for item in apps_returned:
                aid = item['app_id']
                if app_exist(aid):
                    continue
                app_ids.append(aid)
            ok_ids.update(analyse_apps(app_ids))
            if len(ok_ids) >= num:
                return ok_ids


if __name__ == "__main__":
    # I want at least 1 new app
    print(get_new_seeds(1))
