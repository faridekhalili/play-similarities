import logging
import time

from play_scraper import details, similar
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError

from models import *

logging.basicConfig(filename='error.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logging.info("Running Crawler")
logger = logging.getLogger(__name__)
config = toml.load('config.toml')


def app_details(app_id: str) -> dict:
    for i in range(5):
        try:
            return details(app_id)
        except (ReadTimeout, ConnectionError):
            logger.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
        except (HTTPError, ValueError):
            logger.error("url for %s not found" % app_id)
            logger.warning('sleep 5 min')
            time.sleep(5 * 60)
        except AttributeError:
            logger.error("Fetching similar apps for %s failed, AttributeError" % app_id)
            return {}


def get_similar_apps(app_id: str) -> list:
    for i in range(5):
        try:
            return similar(app_id, detailed=False)
        except (ReadTimeout, ConnectionError):
            logger.warning("ReadTimeout error, waiting for 5 seconds.")
            time.sleep(5)
        except (HTTPError, ValueError):
            logger.error("Fetching similar apps for %s failed, HTTPError" % app_id)
            logger.warning('sleep 5 min')
            time.sleep(5 * 60)
            return {}
        except AttributeError:
            logger.error("Fetching similar apps for %s failed, AttributeError" % app_id)
            return {}
