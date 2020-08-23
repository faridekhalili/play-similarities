import toml
from preprocessor import pre_process
import sqlite3
import pandas as pd
from nltk.tokenize import word_tokenize
from gensim.models import Word2Vec


def word2vec_trainer(df):
    description_list = list(map(lambda x: word_tokenize(x),
                                list(df["description"])))
    model = Word2Vec(description_list,
                     min_count=1, size=50, workers=3, window=3, sg=1)
    return model


def main():
    conf = toml.load('config.toml')
    # Read sqlite query results into a pandas DataFrame
    con = sqlite3.connect(conf['database_path'])
    df = pd.read_sql_query("SELECT * from app", con)
    con.close()
    df[['description']] = pre_process(df[['description']])
    model = word2vec_trainer(df)
    model.save(conf['model_path'])


if __name__ == "__main__":
    main()
