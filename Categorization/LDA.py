import toml
import pandas as pd
import gensim
from gensim.models.coherencemodel import CoherenceModel
from nltk.tokenize import word_tokenize
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt


def plot_coherence_scores(max_ntops, coherence_scores, figure_path):
    x = [i + 1 for i in range(max_ntops)]
    plt.figure(figsize=(10, 5))
    plt.plot(x, coherence_scores)
    plt.xticks(np.arange(min(x), max(x) + 1, 1.0))
    plt.xlabel('Number of topics')
    plt.ylabel('Coherence score')
    plt.tight_layout()
    plt.savefig(figure_path)
    plt.show()


def get_bow_corpus(df):
    description_list = list(map(lambda x: word_tokenize(x), list(df["description"])))
    dictionary = gensim.corpora.Dictionary(description_list)
    bow_corpus = [dictionary.doc2bow(doc) for doc in description_list]
    return description_list, dictionary, bow_corpus


def get_tfidf_corpus(bow_corpus):
    tfidf = gensim.models.TfidfModel(bow_corpus)
    corpus_tfidf = tfidf[bow_corpus]
    return corpus_tfidf


def lda(corpus, num_topics, dictionary):
    lda_model = gensim.models.LdaMulticore(corpus,
                                           num_topics=num_topics,
                                           id2word=dictionary,
                                           passes=10, workers=10, iterations=100)
    return lda_model


def search_num_of_topics(max_ntops, corpus, dictionary, description_list):
    coherence_scores = []
    for i in range(max_ntops):
        lda_model = lda(corpus, i + 1, dictionary)
        cm = CoherenceModel(model=lda_model, texts=description_list,
                            corpus=corpus, coherence='c_v')
        coherence_scores.append(cm.get_coherence())
    best_num_topics = coherence_scores.index(max(coherence_scores)) + 1
    return best_num_topics, coherence_scores


def best_lda(df, max_ntops):
    description_list, dictionary, bow_corpus = get_bow_corpus(df)
    corpus_tfidf = get_tfidf_corpus(bow_corpus)
    best_num_topics, coherence_scores = search_num_of_topics(max_ntops, corpus_tfidf,
                                                             dictionary, description_list)
    best_lda_model = lda(corpus_tfidf, best_num_topics, dictionary)
    return best_lda_model, coherence_scores


def main():
    max_ntops = 100
    conf = toml.load('../config-temp.toml')
    df = pd.read_csv('../' + conf["preprocessed_data_path"])
    best_lda_model, coherence_scores = best_lda(df.loc[:, ['description']], max_ntops)
    plot_coherence_scores(max_ntops, coherence_scores, '../'+conf["lda_coherence_figure_path"])
    pprint(best_lda_model.print_topics())
    best_lda_model.save('../' + conf['lda_model_path'])


if __name__ == "__main__":
    main()
