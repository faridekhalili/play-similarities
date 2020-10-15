import gensim
from gensim.models.coherencemodel import CoherenceModel
from pprint import pprint
from Categorization.Word2Vec import *


def get_bow_corpus(texts):
    dictionary = gensim.corpora.Dictionary(texts)
    bow_corpus = [dictionary.doc2bow(doc) for doc in texts]
    return dictionary, bow_corpus


def get_tfidf_corpus(df):
    dictionary, bow_corpus = get_bow_corpus(df)
    tfidf = gensim.models.TfidfModel(bow_corpus)
    corpus_tfidf = tfidf[bow_corpus]
    return dictionary, corpus_tfidf


def get_lsa_model(corpus, num_topics, dictionary):
    lsa_model = gensim.models.LsiModel(corpus, num_topics=num_topics, id2word=dictionary)
    return lsa_model


def get_lda_model(corpus, num_topics, dictionary):
    lda_model = gensim.models.LdaMulticore(corpus,
                                           num_topics=num_topics,
                                           id2word=dictionary,
                                           passes=10, workers=10, iterations=100)
    return lda_model


def search_num_of_topics(algorithm, max_ntops, corpus, dictionary, texts):
    coherence_scores = []
    if algorithm == "lsa":
        for i in range(max_ntops):
            lsa_model = get_lsa_model(corpus, i + 1, dictionary)
            cm = CoherenceModel(model=lsa_model, texts=texts,
                                corpus=corpus, coherence='c_v')
            coherence_scores.append(cm.get_coherence())
        best_num_topics = coherence_scores.index(max(coherence_scores)) + 1
        best_model = get_lsa_model(corpus, best_num_topics, dictionary)
    elif algorithm == "lda":
        for i in range(max_ntops):
            lda_model = get_lda_model(corpus, i + 1, dictionary)
            cm = CoherenceModel(model=lda_model, texts=texts,
                                corpus=corpus, coherence='c_v')
            coherence_scores.append(cm.get_coherence())
        best_num_topics = coherence_scores.index(max(coherence_scores)) + 1
        best_model = get_lda_model(corpus, best_num_topics, dictionary)
    pprint(best_model.print_topics())
    return best_model, coherence_scores


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


def extract_dominant_topics(best_model, corpus_tfidf):
    topic_clusters = []
    for i in range(len(corpus_tfidf)):
        topic_distribution = dict(best_model[corpus_tfidf[i]])
        dominant_topic = max(topic_distribution, key=topic_distribution.get)
        topic_clusters.append(dominant_topic)
    return topic_clusters


def extract_word2vec_models(df, model_path):
    distribution_plot_path = model_path + '../topic_distribution.png'
    plot_distribution(df, distribution_plot_path, 'topic')
    count = 0
    for category, df_category in df.groupby('topic'):
        count += 1
        model_name = model_path + str(count) + ".model"
        model = word2vec_trainer(df=df_category, size=60, model_path=model_path)
        model.save(model_name)


def divide_into_clusters(best_model, df, corpus_tfidf, model_path):
    topic_clusters = extract_dominant_topics(best_model, corpus_tfidf)
    extended_df = pd.DataFrame(list(zip(list(df["description"]), topic_clusters)),
                               columns=['description', 'topic'])
    extract_word2vec_models(extended_df, model_path)


def main():
    max_ntops = 100
    conf = toml.load('../config-temp.toml')
    df = pd.read_csv('../' + conf["preprocessed_data_path"])
    texts = list(df["description"])
    dictionary, corpus_tfidf = get_tfidf_corpus(texts)

    lda_model_path = '../' + conf['lda_model_path']
    lda_coherence_plot_path = lda_model_path + '../lda_coherence.png'
    best_lda_model, lda_coherence_scores = \
        search_num_of_topics("lda", max_ntops, corpus_tfidf, dictionary, texts)
    plot_coherence_scores(max_ntops, lda_coherence_scores, lda_coherence_plot_path)
    divide_into_clusters(best_lda_model, df, corpus_tfidf, lda_model_path)

    lsa_model_path = '../' + conf['lsa_model_path']
    lsa_coherence_plot_path = lsa_model_path + '../lsa_coherence.png'
    best_lsa_model, lsa_coherence_scores = \
        search_num_of_topics("lsa", max_ntops, corpus_tfidf, dictionary, texts)
    plot_coherence_scores(max_ntops, lsa_coherence_scores, lsa_coherence_plot_path)
    divide_into_clusters(best_lsa_model, df, corpus_tfidf, lsa_model_path)


if __name__ == "__main__":
    main()
