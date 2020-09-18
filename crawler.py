import logging
import sys

import peewee
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from regex._regex_core import apply_quantifier

from cloud_db import insert_app_to_cloud, app_exist
from get_new_seeds import get_new_seeds
from models import *

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()

fileHandler = logging.FileHandler("error.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

config = toml.load('config.toml')
from scrap_request import *

app_queue = []


def add_app_to_db(app_id: str, detail: dict, similar_apps) -> bool:
    app = {"app": app_id}
    not_existed_in_cloud = (not app_exist(app))
    if not not_existed_in_cloud:
        return False
    _, created = App.get_or_create(
        app_id=app_id,
        defaults={
            'category': detail['category'],
            'score': detail['score'],
            'description': detail['description'],
            'similar_apps': similar_apps,
            'developer_id': detail['developer_id']
        }
    )
    return True


def is_english(detail):
    try:
        lang = detect(detail['description'])
    except LangDetectException as e:
        logging.error('lang did not detected %s' % detail['app_id'])
        return False
    if lang == 'en':
        return True
    else:
        return False


def similar_apps_to_str(similar_apps):
    ids = [i['app_id'] for i in similar_apps]
    return ','.join(ids)


def node_info_exist(detail, similar_apps):
    if not detail or not len(detail) or not is_english(detail):
        return False
    if not similar_apps or not len(similar_apps):
        return False
    return True


def add_app(node):
    detail = app_details(node)
    similar_apps = get_similar_apps(node)
    similar_apps_str = similar_apps_to_str(similar_apps)
    if not node_info_exist(detail, similar_apps):
        return
    created = add_app_to_db(node, detail, similar_apps_str)
    if created:
        app_queue.extend([i['app_id'] for i in similar_apps])
        logger.info(f'{len(similar_apps)} apps added to queue')
        logger.info(f'{len(app_queue)} apps inside queue')


def bfs():
    while True:
        if app_queue.__len__() > 0:
            node = app_queue.pop()
            add_app(node)
        else:
            logger.info(f'Queue is empty.')
            inject_seeds()


def inject_seeds():
    new_seeds = get_new_seeds(config['seed_injection_num'])
    logger.info(f'{len(new_seeds)} new seeds found')
    for seed in new_seeds:
        add_app(seed)
    logger.info(f'{len(new_seeds)} new seeds added')


def main():
    app_queue.extend(toml.load('seed_list.toml')['seed_apps'])
    db.connect()
    db.create_tables([App])
    bfs()
    print('%d apps gathered' % App.select().count())


if __name__ == '__main__':
    main()
