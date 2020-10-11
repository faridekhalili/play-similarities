import toml
import pandas as pd
from nltk.tokenize import word_tokenize
from gensim.models import Word2Vec


def word2vec_trainer(df):
    description_list = list(map(lambda x: word_tokenize(x),
                                list(df["description"])))
    model = Word2Vec(description_list,
                     min_count=1, size=60, workers=3, window=3, sg=1)
    return model


def main():
    conf = toml.load('../config-temp.toml')
    df = pd.read_csv('../'+conf["preprocessed_data_path"])
    model = word2vec_trainer(df)
    model.save('../'+conf['model_path'])


if __name__ == "__main__":
    main()
