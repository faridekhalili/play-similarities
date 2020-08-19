import logging
import time
import sys

from play_scraper import details, similar
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError

from models import App, Similarity

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


def get_similars(app_id: str) -> dict:
    while True:
        try:
            return similar(app_id, detailed=False)
        except (ReadTimeout, ConnectionError):
            logger.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
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
