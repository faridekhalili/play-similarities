import toml
from peewee import *

db = SqliteDatabase(toml.load('config.toml')['database_path'])


class BaseModel(Model):
    class Meta:
        database = db


class App(BaseModel):
    app_id = CharField(max_length=255, primary_key=True)
    category = CharField(max_length=64)
    score = FloatField(null=True)
    description = TextField()
    similar_apps = TextField()
    developer_id = CharField(max_length=255)


class Similarity(BaseModel):
    app_id1 = ForeignKeyField(App)
    app_id2 = ForeignKeyField(App)

    class Meta:
        primary_key = CompositeKey('app_id1', 'app_id2')
