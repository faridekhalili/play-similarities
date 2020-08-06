import play_scraper
import toml
from tqdm import tqdm, trange
from models import *

db.connect()
db.create_tables([App, Similarity])

conf = toml.load('config.toml')
for criteria in conf['search_criteria']:
    search_result = play_scraper.search(criteria, page=1)
    for i in trange((min(5, len(search_result)))):
        app_result = search_result[i]
        if app_result:
            app = play_scraper.details(app_result['app_id'])
            data, created = App.get_or_create(
                app_id=app['app_id'],
                defaults={
                    'category': app['category'],
                    'score': app['score'],
                    'description': app['description']
                }
            )
            if created:
                similars = play_scraper.similar(app['app_id'], detailed=True)
                for similar in tqdm(similars):
                    data, created = App.get_or_create(
                        app_id=similar['app_id'],
                        defaults={
                            'category': similar['category'],
                            'score': similar['score'],
                            'description': similar['description']
                        }
                    )
                    Similarity.get_or_create(
                        app_id1=app['app_id'],
                        app_id2=similar['app_id']
                    )
