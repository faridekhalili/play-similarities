import queue

import toml

from models import *
from utils import app_details, add_app_to_db, get_similars, add_similars_to_db


class Forest():
    def __init__(self, seeds: list, depth: int=1000):
        self.bfs_queue = queue.Queue()
        for seed in seeds:
            self.bfs_queue.put((seed, seed))
        self.depth = depth

    def bfs(self):
        while not self.bfs_queue.empty():
            node, seed = self.bfs_queue.get()
            if App.select().where(App.seed == seed).count() >= self.depth:
                continue
            details = app_details(node)
            if not details or not len(details):
                continue
            created = add_app_to_db(node, seed, details)
            if created:
                similars = get_similars(node)
                if not similars or not len(similars):
                    continue
                new_similars = add_similars_to_db(node, seed, similars)
                for similar in new_similars:
                    self.bfs_queue.put((similar, seed))


def main():
    conf = toml.load('config.toml')
    db.connect()
    db.create_tables([App, Similarity])
    forest = Forest(conf['seed_apps'], depth=90)
    forest.bfs()
    print('%d apps gathered' % App.select().count())
    print('%d similarities gathered' % Similarity.select().count())


if __name__ == '__main__':
    main()
