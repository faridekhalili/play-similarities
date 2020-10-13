import toml
import pandas as pd
from nltk.tokenize import word_tokenize
from Categorization.Word2Vec import train_and_test_word2vec


def gp_cluster(df, model_path):
    description_list = list(df["description"])
    extended_df = pd.DataFrame(list(zip(list(description_list, list(df["category"])))),
                               columns=['description', 'label'])
    train_and_test_word2vec(extended_df, model_path)


def main():
    conf = toml.load('../config-temp.toml')
    model_path = '../' + conf["google_play_model_path"]
    df = pd.read_csv('../' + conf["preprocessed_data_path"])
    gp_cluster(df, model_path)


if __name__ == "__main__":
    main()
