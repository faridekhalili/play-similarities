import logging
import time

from play_scraper import details, similar, search
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
    for i in range(3):
        try:
            return details(app_id)
        except (ReadTimeout, ConnectionError):
            logger.warning(f"ReadTimeout error, waiting for {str(i ** 3)} seconds.")
        except (HTTPError, ValueError):
            logger.error("url for %s not found" % app_id)
        except AttributeError:
            logger.error("Fetching similar apps for %s failed, AttributeError" % app_id)
        logger.warning(f'sleep {str(i ** 3)}  sec')
        time.sleep(i ** 3)


def get_similar_apps(app_id: str) -> list:
    for i in range(3):
        try:
            return similar(app_id, detailed=False)
        except (ReadTimeout, ConnectionError):
            logger.warning(f"ReadTimeout error, waiting for {str(i ** 3)}  seconds.")
        except (HTTPError, ValueError):
            logger.error("Fetching similar apps for %s failed, HTTPError" % app_id)
        except AttributeError:
            logger.error("Fetching similar apps for %s failed, AttributeError" % app_id)
        logger.warning(f'sleep {str(i ** 3)}  sec')
        time.sleep(i ** 3)


def search_app(query, page):
    for i in range(5):
        try:
            return search(query, page=page)
        except (ReadTimeout, ConnectionError):
            logger.warning(f"ReadTimeout error, waiting for {str(i ** 4)}  seconds.")
            time.sleep(i ** 4)
        except (HTTPError, ValueError):
            logger.error("Searching apps for %s failed, HTTPError" % query)
            logger.warning(f'sleep {str(i ** 4)}  sec')
            time.sleep(i ** 4)
            return {}
        except AttributeError:
            logger.error("Searching apps for %s failed, AttributeError" % query)
            return {}
        except TypeError:
            logger.error("Searching apps for %s failed, Type Error" % query)
            return {}
