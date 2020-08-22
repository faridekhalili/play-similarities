import toml
from gensim.models import Word2Vec
import pandas as pd
from nltk.tokenize import word_tokenize


def word2vec_trainer(df):
    description_list = list(map(lambda x: word_tokenize(x),
                                list(df["description"])))
    model = Word2Vec(description_list,
                     min_count=1, size=50, workers=3, window=3, sg=1)
    return model


def main():
    conf = toml.load('config.toml')
    df = pd.read_csv("preprocessed.csv")
    model = word2vec_trainer(df)
    model.save(conf['model_path'])


if __name__ == "__main__":
    main()