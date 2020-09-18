import ssl

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

client = MongoClient(
    "mongodb+srv://simi:aYa0g4hclEuVQRVG@cluster0.7dowm.gcp.mongodb.net/Crawler?retryWrites=true&w=majority",
    ssl_cert_reqs=ssl.CERT_NONE)
db = client['Crawler']
apps = db.Apps


def insert_app_to_cloud(app):
    try:
        apps.insert_one({'app': app})
    except DuplicateKeyError:
        return False
    return True


def app_exist(app):
    return apps.find({'app': app}).count() > 0
