import logging

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger()


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
