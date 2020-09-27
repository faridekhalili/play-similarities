import toml
import pandas as pd
import gensim
from nltk.tokenize import word_tokenize


def get_bow_corpus(df):
    description_list = list(map(lambda x: word_tokenize(x), list(df["description"])))
    dictionary = gensim.corpora.Dictionary(description_list)
    bow_corpus = [dictionary.doc2bow(doc) for doc in description_list]
    return dictionary, bow_corpus


def get_tfidf_corpus(bow_corpus):
    tfidf = gensim.models.TfidfModel(bow_corpus)
    corpus_tfidf = tfidf[bow_corpus]
    return corpus_tfidf


def lda(df):
    dictionary, bow_corpus = get_bow_corpus(df)
    corpus_tfidf = get_tfidf_corpus(bow_corpus)
    lda_model = gensim.models.LdaMulticore(corpus_tfidf,
                                           num_topics=10, id2word=dictionary, passes=2, workers=4)
    return lda_model


def main():
    conf = toml.load('config-temp.toml')
    df = pd.read_csv(conf["preprocessed_data_path"])
    lda_model = lda(df.loc[:, ['description']])
    lda_model.save(conf['lda_model_path'])


if __name__ == "__main__":
    main()
