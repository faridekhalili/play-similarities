from cloud_db import app_exist, insert_app_to_cloud
from get_new_seeds import get_new_seeds
from scrap_request import *
from utils.lang_detect import is_english

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()

fileHandler = logging.FileHandler("error.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

config = toml.load('config.toml')

app_queue = []


def add_app_to_db(app_id: str, detail: dict, similar_apps) -> bool:
    already_in_db = not insert_app_to_cloud(app_id)
    if already_in_db:
        return False
    _, created = App.get_or_create(
        app_id=app_id,
        defaults={
            'category': detail['category'],
            'score': detail['score'],
            'description': detail['description'],
            'similar_apps': similar_apps,
            'developer_id': detail['developer_id']
        }
    )
    return created


def similar_apps_to_str(similar_apps):
    if similar_apps is None:
        return None
    ids = [i['app_id'] for i in similar_apps]
    return ','.join(ids)


def node_info_exist(detail):
    if not detail or not len(detail) or not is_english(detail):
        return False
    return True


def add_app(node):
    not_existed_in_cloud = (not app_exist(node))
    if not_existed_in_cloud:
        detail = app_details(node)
        similar_apps = get_similar_apps(node)
        similar_apps_str = similar_apps_to_str(similar_apps)
        if not node_info_exist(detail):
            logger.info(f'No info or not english for {node}')
            return
        created = add_app_to_db(node, detail, similar_apps_str)
        if created and similar_apps:
            app_queue.extend([i['app_id'] for i in similar_apps])
            logger.info(f'{len(similar_apps)} apps added to queue total {len(app_queue)}')


def bfs():
    while True:
        if app_queue.__len__() > 0:
            node = app_queue.pop()
            add_app(node)
        else:
            logger.info(f'Queue is empty.')
            inject_seeds()


def inject_seeds():
    new_seeds = get_new_seeds(config['seed_injection_num'])
    logger.info(f'{len(new_seeds)} new seeds found')
    for seed in new_seeds:
        add_app(seed)
    logger.info(f'{len(new_seeds)} new seeds added')


def main():
    app_queue.extend(toml.load('seed_list.toml')['seed_apps'])
    db.connect()
    db.create_tables([App])
    bfs()
    print('%d apps gathered' % App.select().count())


if __name__ == '__main__':
    main()
