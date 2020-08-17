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


def insert_similar(app, similar, sim_cnt):
    sim_data, sim_created = Similarity.get_or_create(
        app_id1=app['app_id'],
        app_id2=similar['app_id'],
        defaults={
            'row_number': sim_cnt
        }
    )
    if sim_created:
        sim_cnt += 1
    return sim_cnt


def insert_similar_apps(app, seed, app_cnt, sim_cnt, attr_error_cnt):
    while True:
        try:
            print()
            print(time.strftime("%H:%M:%S", time.localtime()))
            print("GETTING SIMILAR APPS\n")
            similar_apps = play_scraper.similar(app['app_id'], detailed=True)
            print()
            print(time.strftime("%H:%M:%S", time.localtime()))
            print("INSERTING INTO SIMILAR TABLE\n")
            for similar in tqdm(similar_apps, position=1):
                app_cnt = insert_app(similar, seed, app_cnt)
                sim_cnt = insert_similar(app, similar, sim_cnt)
            break
        except AttributeError:
            root.error("Fetching similar apps for %s failed, AttributeError" % app['app_id'])
            attr_error_cnt += 1
            print("\nAttributeError\n")
            break
        except (ReadTimeout, ConnectionError):
            root.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
    return app_cnt, sim_cnt, attr_error_cnt


def insert_app(app, seed, app_cnt):
    data, created = App.get_or_create(
        app_id=app['app_id'],
        defaults={
            'category': app['category'],
            'score': app['score'],
            'seed': seed,
            'description': app['description']
        }
    )
    if created:
        app_cnt += 1
        print("\n")
        print(time.strftime("%H:%M:%S", time.localtime()))
        print("app " + str(app_cnt) + " created.")
        print("\n")
    else:
        print("\n")
        print(time.strftime("%H:%M:%S", time.localtime()))
        print("app already exists")
        print("\n")
    return app_cnt


def one_step_bfs(root_app, seed, app_cnt, sim_cnt, attr_error_cnt):
    app_cnt = insert_app(root_app, seed, app_cnt)
    app_cnt, sim_cnt, attr_error_cnt = insert_similar_apps(root_app,
                                       seed, app_cnt, sim_cnt, attr_error_cnt)
    return app_cnt, sim_cnt, attr_error_cnt


def gather_data_for_seed(seed, sim_count, indicator, num_for_each_seed):
    count = 0
    attr_error_cnt = 0
    prev_count = count
    last_update_time = datetime.datetime.now()
    while True:
        try:
            app = play_scraper.details(seed)
            count, sim_count, attr_error_cnt = one_step_bfs(app, seed, count, sim_count, attr_error_cnt)
            while count < num_for_each_seed:
                print(40 * "#")
                print("Num of count : " + str(count) + " taking another step.")
                print(40 * "#")
                if nothing_updated_for_long(last_update_time):
                    break
                query = Similarity.select().where(Similarity.row_number == indicator)
                for sim in query:
                    app2_id = sim.app_id2
                    while True:
                        try:
                            app = play_scraper.details(app2_id)
                            break
                        except (ReadTimeout, ConnectionError):
                            root.warning("ReadTimeout error, waiting for 5 seconds.")
                            time.sleep(5)
                    count, sim_count, attr_error_cnt = one_step_bfs(app,
                                                       seed, count, sim_count, attr_error_cnt)
                    prev_count, last_update_time = get_time_of_update(count,
                                                    prev_count, last_update_time)
                indicator += 1
            print(40 * "#")
            print("Num of count : " + str(count) + " moving on to the next seed.")
            print(40 * "#")
            break
        except (ReadTimeout, ConnectionError):
            root.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
        except (HTTPError, ValueError):
            root.error("url for %s not found" % seed)
            break
    attribute_error_list.append(attr_error_cnt)
    return sim_count


def crawl(seeds, num_for_each_seed):
    num_seeds = len(seeds)
    indicator = 0
    sim_count = 0
    for i in trange(num_seeds):
        if i > 0:
            indicator = sim_count
        sim_count = gather_data_for_seed(seeds[i], sim_count, indicator, num_for_each_seed)
    print(attribute_error_list)
    with open('AttributeErrorCounts.txt', 'w') as file:
        for attribute_error_cnt in attribute_error_list:
            file.write("%i\n" % attribute_error_cnt)



db.connect()
db.create_tables([App, Similarity])

conf = toml.load('config.toml')
seeds = conf['seed_apps']

crawl(seeds, 1000)
