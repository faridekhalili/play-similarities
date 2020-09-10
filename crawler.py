import logging
import time
import sys

import peewee

from mongo import insert_app_to_cloud
from models import *
from play_scraper import details, similar
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.WARNING)
file_handler = logging.FileHandler('error.log')
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)


def app_details(app_id: str) -> dict:
    try:
        return details(app_id)
    except (ReadTimeout, ConnectionError):
        logger.warning("ReadTimeout error, waiting for 5 seconds.")
        time.sleep(5)
    except (HTTPError, ValueError):
        logger.error("url for %s not found" % app_id)
        return {}
    except AttributeError:
        logger.error("Fetching similar apps for %s failed, AttributeError" % app_id)
        return {}


def get_similar_apps(app_id: str) -> list:
    while True:
        try:
            return similar(app_id, detailed=False)
        except (ReadTimeout, ConnectionError):
            logger.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
        except (HTTPError, ValueError):
            logger.error("Fetching similar apps for %s failed, HTTPError" % app_id)
            return {}
        except AttributeError:
            logger.error("Fetching similar apps for %s failed, AttributeError" % app_id)
            return {}


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
    if not_existed_in_cloud:
        return False
    _, created = App.get_or_create(
        app_id=app_id,
        defaults={
            'category': detail['category'],
            'score': detail['score'],
            'seed': seed,
            'description': detail['description'],
            'row_number': app_cnt
        }
    )
    return created


class Forest:
    def __init__(self, seeds: list):
        self.app_cnt = 0
        for seed in seeds:
            self.add_app(seed, seed)

    def add_app(self, node, seed):
        detail = app_details(node)
        if not detail or not len(detail):
            return
        created = add_app_to_db(node, seed, detail, self.app_cnt)
        if created:
            print("app_cnt: " + str(self.app_cnt) + "\n")
            self.app_cnt += 1

    def add_similar_apps(self, node, seed):
        similar_apps = get_similar_apps(node)
        if not similar_apps or not len(similar_apps):
            return
        new_similar_apps = add_similar_apps_to_db(node, similar_apps)
        for sim in new_similar_apps:
            self.add_app(sim, seed)

    def bfs(self):
        index = 0
        while True:
            try:
                print("index: " + str(index))
                current_node = App.get(App.row_number == index)
                node = current_node.app_id
                seed = current_node.seed
                self.add_similar_apps(node, seed)
                index += 1
                if index == 15:
                    print("index reached it's limit: "+
                          str(index)+".\t app_cnt: "+str(self.app_cnt)+".\n")
                    break
            except peewee.DoesNotExist:
                logger.error("index %s is not available in App table where app_cnt is %s." % index % self.app_cnt)
                break


def main():
    conf = toml.load('config.toml')
    db.connect()
    db.create_tables([App, Similarity])
    forest = Forest(conf['seed_apps'])
    forest.bfs()
    print('%d apps gathered' % App.select().count())
    print('%d similarities gathered' % Similarity.select().count())


if __name__ == '__main__':
    main()
