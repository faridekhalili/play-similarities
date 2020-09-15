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
        apps.insert_one(app)
    except DuplicateKeyError:
        return False
    return True


if __name__ == '__main__':
    for i in range(90000):
        app = {"app": "com.toddsssdadsadasdasdasdasdsadasdasdsa" + str(i)}
        result = insert_app_to_cloud(app)
        print(i)

