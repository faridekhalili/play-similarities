import logging

import peewee
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from cloud_db import insert_app_to_cloud
from get_new_seeds import get_new_seeds
from models import *

logging.basicConfig(filename='error.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logging.info("Running Crawler")
logger = logging.getLogger(__name__)
config = toml.load('config.toml')

from scrap_request import *


def add_similar_apps_to_db(app_id: str, similar_apps: list) -> list:
    new_similar_apps = []
    for sim in similar_apps:
        if not App.select().where(App.app_id == sim['app_id']).exists():
            new_similar_apps.append(sim['app_id'])
        Similarity.get_or_create(
            app_id1=app_id,
            app_id2=sim['app_id'],
        )
    return new_similar_apps


def add_app_to_db(app_id: str, seed: str, detail: dict, app_cnt) -> bool:
    app = {"app": app_id}
    not_existed_in_cloud = insert_app_to_cloud(app)
    if not not_existed_in_cloud:
        return False
    _, created = App.get_or_create(
        app_id=app_id,
        defaults={
            'category': detail['category'],
            'score': detail['score'],
            'seed': seed,
            'description': detail['description'],
            'row_number': app_cnt,
            'expanded': False
        }
    )
    return created


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


class Forest:
    def __init__(self, seeds: list):
        try:
            self.get_index()
        except TypeError:
            self.app_cnt = 0
        for seed in seeds:
            self.add_app(seed, seed)

    def add_app(self, node, seed):
        detail = app_details(node)
        if not detail or not len(detail) or not is_english(detail):
            return
        created = add_app_to_db(node, seed, detail, self.app_cnt)
        if created:
            print("app : " + str(self.app_cnt) + " " + node + " created.")
            self.app_cnt += 1

    def add_similar_apps(self, node, seed):
        similar_apps = get_similar_apps(node)
        if not similar_apps or not len(similar_apps):
            return
        new_similar_apps = add_similar_apps_to_db(node, similar_apps)
        for sim in new_similar_apps:
            self.add_app(sim, seed)
            # time.sleep(rand()*20)

    def get_index(self):
        query = App.select(fn.MIN(App.row_number)).where(App.expanded == False)
        index = query.scalar()
        max_app_cnt = App.select(fn.MAX(App.row_number)).scalar()
        self.app_cnt = max_app_cnt + 1
        return index

    def bfs(self):
        index = self.get_index()
        while True:
            try:
                print("index: " + str(index))
                current_node = App.get(App.row_number == index)
                node = current_node.app_id
                seed = current_node.seed
                self.add_similar_apps(node, seed)
                try:
                    query = App.update(expanded=True).where(App.row_number == index)
                    query.execute()
                except peewee.DoesNotExist:
                    logger.error("index %s is not available in App table." % index)
                index += 1
            except peewee.DoesNotExist:
                logger.warning(f'index {index} is not available in App table where app_cnt is {self.app_cnt}.')
                self.inject_seeds()
                index = self.get_index()

    def inject_seeds(self):
        new_seeds = get_new_seeds(config['seed_injection_num'])
        for seed in new_seeds:
            self.add_app(seed, seed)
        logger.info(f'{len(new_seeds)} new seeds added')


def main():
    seed_list = toml.load('seed_list.toml')
    db.connect()
    db.create_tables([App, Similarity])
    forest = Forest(seed_list['seed_apps'])
    forest.bfs()
    print('%d apps gathered' % App.select().count())
    print('%d similarities gathered' % Similarity.select().count())


if __name__ == '__main__':
    main()
