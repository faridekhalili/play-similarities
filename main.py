import datetime
import logging
import sys
import time

import play_scraper
from requests.exceptions import ReadTimeout, HTTPError, ConnectionError
from tqdm import tqdm, trange

from models import *

root = logging.getLogger()
root.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.WARNING)
file_handler = logging.FileHandler('error.log')
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
root.addHandler(handler)
root.addHandler(file_handler)


def get_app_details(app, seed, counter):
    app_detail = play_scraper.details(app['app_id'])
    defaults = {
        'category': app_detail['category'],
        'score': app_detail['score'],
        'seed': seed,
        'description': app_detail['description'],
        'row_number': counter
    }
    return defaults


def app_not_already_exists(app):
    query = App.select().where(App.app_id == app['app_id'])
    return not query.exists()


def some_new_app(count, prev_count):
    return count != prev_count


def get_time_of_update(count, prev_count, last_update_time):
    if some_new_app(count, prev_count):
        prev_count = count
        last_update_time = datetime.datetime.now()
    return prev_count, last_update_time


def nothing_updated_for_long(last_update_time):
    time_delta = (datetime.datetime.now() - last_update_time)
    return (time_delta.seconds / 60) > 20


def insert_similar(app, similar):
    Similarity.get_or_create(
        app_id1=app['app_id'],
        app_id2=similar['app_id'],
    )


def insert_similar_apps(app, seed, app_cnt, counter):
    while True:
        try:
            similar_apps = play_scraper.similar(app['app_id'], detailed=False)
            for similar in tqdm(similar_apps, position=1):
                app_cnt, counter = insert_app(similar, seed, app_cnt, counter)
                insert_similar(app, similar)
            break
        except AttributeError:
            root.error("Fetching similar apps for %s failed, AttributeError" % app['app_id'])
            break
        except (ReadTimeout, ConnectionError):
            root.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
    return app_cnt, counter


def insert_app(app, seed, app_cnt, counter):
    if app_not_already_exists(app):
        defaults = get_app_details(app, seed, counter)
        App.get_or_create(
            app_id=app['app_id'],
            defaults=defaults
        )
        app_cnt += 1
        counter += 1
    return app_cnt, counter


def one_step_bfs(root_app, seed, app_cnt, counter):
    app_cnt, counter = insert_app(root_app, seed, app_cnt, counter)
    app_cnt, counter = insert_similar_apps(root_app, seed, app_cnt, counter)
    return app_cnt, counter


def proceed_in_graph(indicator, seed, app_cnt, counter, prev_count, last_update_time):
    query = App.select().where(App.row_number == indicator)
    for application in query:
        root_app_id = application.app_id
        while True:
            try:
                app = play_scraper.details(root_app_id)
                break
            except (ReadTimeout, ConnectionError):
                root.warning("ReadTimeout error, waiting for 5 seconds.")
                time.sleep(5)
        app_cnt, counter = one_step_bfs(app, seed, app_cnt, counter)
        prev_count, last_update_time = \
        get_time_of_update(app_cnt, prev_count, last_update_time)
    indicator += 1
    return indicator, app_cnt, counter, prev_count, last_update_time


def gather_data_for_seed(seed, counter, indicator, num_for_each_seed):
    app_cnt = 0
    prev_count = app_cnt
    last_update_time = datetime.datetime.now()
    while True:
        try:
            app = play_scraper.details(seed)
            app_cnt, counter = one_step_bfs(app, seed, app_cnt, counter)
            prev_count, last_update_time = \
            get_time_of_update(app_cnt, prev_count, last_update_time)
            while app_cnt < num_for_each_seed:
                if nothing_updated_for_long(last_update_time):
                    break
                if indicator > counter:
                    break
                indicator, app_cnt, counter, prev_count, last_update_time = \
                    proceed_in_graph(indicator,
                    seed, app_cnt, counter, prev_count, last_update_time)
            break
        except (ReadTimeout, ConnectionError):
            root.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
        except (HTTPError, ValueError):
            root.error("url for %s not found" % seed)
            break
    return counter


def crawl(seeds, num_for_each_seed):
    num_seeds = len(seeds)
    counter = 0
    indicator = 1
    for i in trange(num_seeds):
        print("\n\nprocessing " + str(i) + "th seed " + str(seeds[i]) + ".\n\n")
        if i > 0:
            indicator = counter
        counter = gather_data_for_seed(seeds[i], counter, indicator, num_for_each_seed)


db.connect()
db.create_tables([App, Similarity])

conf = toml.load('config.toml')
seeds = conf['seed_apps']

crawl(seeds, 1000)
