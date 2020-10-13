import toml
import pandas as pd
from nltk.tokenize import word_tokenize
import gensim
from gensim.models.coherencemodel import CoherenceModel
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint
from Categorization.Word2Vec import train_and_test_word2vec


def best_lda(df, max_ntops, plot_path):
    description_list = list(df["description"])
    dictionary, bow_corpus = get_bow_corpus(description_list)
    corpus_tfidf = get_tfidf_corpus(bow_corpus)
    best_num_topics = search_num_of_topics(max_ntops, corpus_tfidf,
                                           dictionary, description_list, plot_path)
    best_lda_model = lda(corpus_tfidf, best_num_topics, dictionary)
    pprint(best_lda_model.print_topics())
    return best_lda_model, corpus_tfidf


def get_bow_corpus(texts):
    dictionary = gensim.corpora.Dictionary(texts)
    bow_corpus = [dictionary.doc2bow(doc) for doc in texts]
    return dictionary, bow_corpus


def get_tfidf_corpus(bow_corpus):
    tfidf = gensim.models.TfidfModel(bow_corpus)
    corpus_tfidf = tfidf[bow_corpus]
    return corpus_tfidf


def search_num_of_topics(max_ntops, corpus, dictionary, texts, plot_path):
    coherence_scores = []
    for i in range(max_ntops):
        lda_model = lda(corpus, i + 1, dictionary)
        cm = CoherenceModel(model=lda_model, texts=texts,
                            corpus=corpus, coherence='c_v')
        coherence_scores.append(cm.get_coherence())
    best_num_topics = coherence_scores.index(max(coherence_scores)) + 1
    plot_coherence_scores(max_ntops, coherence_scores, plot_path)
    return best_num_topics


def lda(corpus, num_topics, dictionary):
    lda_model = gensim.models.LdaMulticore(corpus,
                                           num_topics=num_topics,
                                           id2word=dictionary,
                                           passes=10, workers=10, iterations=100)
    return lda_model


def plot_coherence_scores(max_ntops, coherence_scores, plot_path):
    x = [i + 1 for i in range(max_ntops)]
    plt.figure(figsize=(10, 5))
    plt.plot(x, coherence_scores)
    plt.xticks(np.arange(min(x), max(x) + 1, 1.0))
    plt.xlabel('Number of topics')
    plt.ylabel('Coherence score')
    plt.tight_layout()
    plt.savefig(plot_path)


def divide_into_clusters(best_lda_model, df, corpus_tfidf):
    description_list = list(df["description"])
    topic_clusters = extract_dominant_topics(best_lda_model, corpus_tfidf)
    extended_df = pd.DataFrame(list(zip(list(description_list, topic_clusters))),
                               columns=['description', 'label'])
    return extended_df


def extract_dominant_topics(best_lda_model, corpus_tfidf):
    topic_clusters = []
    for i in range(len(corpus_tfidf)):
        topic_distribution = dict(best_lda_model[corpus_tfidf[i]])
        dominant_topic = max(topic_distribution, key=topic_distribution.get)
        topic_clusters.append(dominant_topic)
    return topic_clusters


def main():
    max_ntops = 100
    conf = toml.load('../config-temp.toml')
    model_path = '../' + conf['lda_model_path']
    plot_path = model_path + '../lda_coherence.png'
    df = pd.read_csv('../' + conf["preprocessed_data_path"])
    best_lda_model, corpus_tfidf = best_lda(df.loc[:, ['description']], max_ntops,
                                            plot_path)
    extended_df = divide_into_clusters(best_lda_model, df, corpus_tfidf)
    train_and_test_word2vec(extended_df, model_path)


if __name__ == "__main__":
    main()
