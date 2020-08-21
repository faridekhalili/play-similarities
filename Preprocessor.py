import re
import toml
import string
import pandas as pd
import sqlite3
import nltk

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer


def remove_punctuation(s):
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    return s.translate(translator)


def remove_stop_words(input_str):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(input_str)
    result = [i for i in tokens if i not in stop_words]
    joined_result = ' '.join(result)
    if joined_result == '':
        return input_str
    else:
        return joined_result


def lemmetizing(input_str):
    lemmatizer = WordNetLemmatizer()
    input_str = word_tokenize(input_str)
    result = [lemmatizer.lemmatize(i) for i in input_str]
    return ' '.join(result)


def remove_redundant_words(input_str):
    list_str = input_str.split()
    unique_list = list(set(list_str))
    result = ' '.join(unique_list)
    return result


def pre_process(data):
    lower_data = data.applymap(lambda s: s.lower())
    removed_number_data = lower_data.applymap(lambda s: re.sub(r'\d+', '', s))
    removed_punctuation_data = removed_number_data.applymap(lambda s: remove_punctuation(s))
    striped_data = removed_punctuation_data.applymap(lambda s: s.strip())
    removed_extra_white_space = striped_data.applymap(lambda s: ' '.join(s.split()))
    removed_stop_words = removed_extra_white_space.applymap(lambda s: remove_stop_words(s))
    lemmetized_data = removed_stop_words.applymap(lambda s: lemmetizing(s))
    removed_redundant = lemmetized_data.applymap(lambda s: remove_redundant_words(s))
    return removed_redundant


if __name__ == "__main__":
    # Read sqlite query results into a pandas DataFrame
    conf = toml.load('config.toml')
    con = sqlite3.connect(conf['database_path'])
    df = pd.read_sql_query("SELECT * from app", con)
    con.close()

    df[['description']] = pre_process(df[['description']])
    df.to_csv("df.csv")
    print(remove_redundant_words("shopping rocks rocks ab ab ab"))
