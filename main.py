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

attribute_error_list = []


def some_new_app(count, prev_count):
    if count == prev_count:
        print("\nNOTHING NEW\n")
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


def insert_similar_apps(app, counter, seed, app_cnt, attr_error_cnt):
    while True:
        try:
            print()
            print(time.strftime("%H:%M:%S", time.localtime()))
            print("GETTING SIMILAR APPS\n")
            similar_apps = play_scraper.similar(app['app_id'], detailed=False)
            print()
            print(time.strftime("%H:%M:%S", time.localtime()))
            print("INSERTING INTO SIMILAR TABLE\n")
            for similar in tqdm(similar_apps, position=1):
                app_cnt, counter = insert_app(similar, counter, seed, app_cnt)
                insert_similar(app, similar)
            break
        except AttributeError:
            root.error("Fetching similar apps for %s failed, AttributeError" % app['app_id'])
            attr_error_cnt += 1
            print("\nAttributeError\n")
            break
        except (ReadTimeout, ConnectionError):
            root.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
    return app_cnt, counter, attr_error_cnt


def insert_app(app, counter, seed, app_cnt):
    query = App.select().where(App.app_id == app['app_id'])
    if not query.exists():
        app = play_scraper.details(app['app_id'])
        data, created = App.get_or_create(
            app_id=app['app_id'],
            defaults={
                'category': app['category'],
                'score': app['score'],
                'seed': seed,
                'description': app['description'],
                'row_number': counter
            }
        )
        if created:
            app_cnt += 1
            counter += 1
            print("\n")
            print(time.strftime("%H:%M:%S", time.localtime()))
            print("app " + str(app_cnt) + " created.")
            print("\n")
        else:
            print("\n")
            print(time.strftime("%H:%M:%S", time.localtime()))
            print("app already exists")
            print("\n")
    return app_cnt, counter


def one_step_bfs(root_app, counter, seed, app_cnt, attr_error_cnt):
    app_cnt, counter = insert_app(root_app, counter, seed, app_cnt)
    app_cnt, counter, attr_error_cnt = insert_similar_apps(root_app, counter,
                                                  seed, app_cnt, attr_error_cnt)
    return app_cnt, counter, attr_error_cnt


def gather_data_for_seed(seed, counter, indicator, num_for_each_seed):
    app_cnt = 0
    prev_count = app_cnt
    attr_error_cnt = 0
    last_update_time = datetime.datetime.now()
    while True:
        try:
            app = play_scraper.details(seed)
            app_cnt, counter, attr_error_cnt = one_step_bfs(app,
                                                          counter, seed, app_cnt,
                                                            attr_error_cnt)
            while app_cnt < num_for_each_seed:
                print(40 * "#")
                print("Num of count : " + str(app_cnt) + " taking another step.")
                print(40 * "#")
                if nothing_updated_for_long(last_update_time):
                    print("\n nothing_updated_for_long\n")
                    break
                if indicator > counter:
                    print("\nindicator > counter\n")
                    print("indicator: "+ str(indicator))
                    print("counter : " + str(counter))
                    break
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
                    app_cnt, counter, attr_error_cnt = one_step_bfs(app,
                                                    counter, seed,
                                                    app_cnt, attr_error_cnt)
                    prev_count, last_update_time = get_time_of_update(app_cnt,
                                                    prev_count, last_update_time)
                indicator += 1
            print(40 * "#")
            print("Num of count : " + str(app_cnt) + " moving on to the next seed.")
            print(40 * "#")
            break
        except (ReadTimeout, ConnectionError):
            root.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
        except (HTTPError, ValueError):
            root.error("url for %s not found" % seed)
            break
    attribute_error_list.append(attr_error_cnt)
    return counter


def crawl(seeds, num_for_each_seed):
    num_seeds = len(seeds)
    counter = 0
    indicator = 1
    for i in trange(num_seeds):
        if i > 0:
            indicator = counter
        counter = gather_data_for_seed(seeds[i], counter, indicator, num_for_each_seed)
    print(attribute_error_list)
    with open('AttributeErrorCounts.txt', 'w') as file:
        for attribute_error_cnt in attribute_error_list:
            file.write("%i\n" % attribute_error_cnt)


db.connect()
db.create_tables([App, Similarity])

conf = toml.load('config.toml')
seeds = conf['seed_apps']

crawl(seeds, 1000)
