import ssl
from pymongo import MongoClient


def get_client():
    return MongoClient(
        "mongodb+srv://simi:aYa0g4hclEuVQRVG@cluster0.7dowm.gcp.mongodb.net/Crawler?retryWrites=true&w=majority",
        ssl_cert_reqs=ssl.CERT_NONE)


def get_app_collection():
    client = get_client()
    db = client['Crawler']
    return db.Apps
