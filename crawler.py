import queue
import logging
import time
import sys
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


def get_similars(app_id: str) -> list:
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


def add_similars_to_db(app_id: str, seed: str, similars: list) -> list:
    new_similars = []
    for sim in similars:
        if not App.select().where(App.app_id == sim['app_id']).exists():
            new_similars.append(sim['app_id'])
            Similarity.get_or_create(
                app_id1=app_id,
                app_id2=sim['app_id'],
            )
    return new_similars


def add_app_to_db(app_id: str, seed: str, details: dict) -> bool:
    _, created = App.get_or_create(
        app_id=app_id,
        defaults={
            'category': details['category'],
            'score': details['score'],
            'seed': seed,
            'description': details['description']
        }
    )
    return created


class Forest:
    def __init__(self, seeds: list, depth: int = 1000):
        self.bfs_queue = queue.Queue()
        for seed in seeds:
            self.bfs_queue.put((seed, seed))
        self.depth = depth

    def skip_node(self, fully_extracted_seeds, seed):
        if seed in fully_extracted_seeds:
            return True
        app_cnt = App.select().where(App.seed == seed).count()
        if app_cnt >= self.depth:
            fully_extracted_seeds.append(seed)
            print('continuing to next seed with {} apps gathered for {}'.format(app_cnt, seed))
            return True

    def add_similars_to_queue(self, node, seed):
        print('created %s' % node)
        similars = get_similars(node)
        if not similars or not len(similars):
            pass
        new_similars = add_similars_to_db(node, seed, similars)
        print('found %d new similar apps' % len(new_similars))
        for similar in new_similars:
            self.bfs_queue.put((similar, seed))

    def bfs(self):
        fully_extracted_seeds = []
        while not self.bfs_queue.empty():
            node, seed = self.bfs_queue.get()
            if self.skip_node(fully_extracted_seeds, seed):
                continue
            details = app_details(node)
            if not details or not len(details):
                continue
            created = add_app_to_db(node, seed, details)
            if created:
                self.add_similars_to_queue(node, seed)


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
