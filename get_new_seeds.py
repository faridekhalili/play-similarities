import ssl
from pymongo import MongoClient
import os
import play_scraper
from random_word import RandomWords
import time
import random
import string

from cloud_db import app_exist

r = RandomWords()


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def sleep():
    time.sleep(random.uniform(0, 1))


def analyse_apps(app_ids: list):
    apps_ids_not_games = []
    for app_id in app_ids:
        details = play_scraper.details(app_id)
        sleep()
        category = list(details['category'])
        if any("GAME" not in s for s in category):
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
            sleep()
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