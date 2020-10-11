import toml
import pandas as pd
import gensim
from gensim.models.coherencemodel import CoherenceModel
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


def lda(dictionary, corpus, num_topics):
    lda_model = gensim.models.LdaMulticore(corpus,
                                           num_topics=num_topics,
                                           id2word=dictionary,
                                           passes=10, workers=4)
    return lda_model


def search_num_of_topics(dictionary, corpus_tfidf, max_ntops):
    coherence_scores = []
    for i in range(max_ntops):
        lda_model = lda(dictionary, corpus_tfidf, i + 1)
        cm = CoherenceModel(model=lda_model, corpus=corpus_tfidf, coherence='u_mass')
        coherence_scores.append(cm.get_coherence())
    best_num_topics = coherence_scores.index(max(coherence_scores)) + 1
    print("best_num_topics: " + str(best_num_topics) + ', with coherence score : ' + str(
        coherence_scores[best_num_topics - 1]))
    return best_num_topics


def best_lda(df):
    dictionary, bow_corpus = get_bow_corpus(df)
    corpus_tfidf = get_tfidf_corpus(bow_corpus)
    best_num_topics = search_num_of_topics(dictionary, corpus_tfidf, 100)
    best_lda_model = lda(dictionary, corpus_tfidf, best_num_topics)
    return best_lda_model


def main():
    conf = toml.load('../config-temp.toml')
    df = pd.read_csv('../'+conf["preprocessed_data_path"])
    best_lda_model = best_lda(df.loc[:, ['description']])
    best_lda_model.save('../'+conf['lda_model_path'])


if __name__ == "__main__":
    main()
