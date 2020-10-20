import gensim
from gensim.models.coherencemodel import CoherenceModel
from pprint import pprint
from Categorization.Word2Vec import *
from abc import ABC, abstractmethod


class TopicModel(ABC):
    def __init__(self, dataset, folder_path):
        self.__max_num_topics = 100
        self.__df = dataset
        self.__folder_path = folder_path
        self.__dictionary = gensim.corpora.Dictionary(self.__df)
        self.save_dictionary()
        self.__bow_corpus = [self.__dictionary.doc2bow(doc) for doc in self.__df]
        tfidf = gensim.models.TfidfModel(self.__bow_corpus)
        self.save_tfidf_corpus(tfidf)
        self.__corpus_tfidf = tfidf[self.__bow_corpus]

    def save_dictionary(self):
        dictionary_path = self.__folder_path + "dataset.dict"
        self.__dictionary.save(dictionary_path)

    def save_tfidf_corpus(self, tfidf):
        tfidf_path = self.__folder_path + "dataset.tfidf_model"
        tfidf.save(tfidf_path)

    def search_num_of_topics(self):
        coherence_scores = []
        for i in range(self.__max_num_topics):
            model = self.get_model(i + 1)
            cm = CoherenceModel(model=model, texts=self.__df,
                                corpus=self.__corpus_tfidf, coherence='c_v')
            coherence_scores.append(cm.get_coherence())
        best_num_topics = coherence_scores.index(max(coherence_scores)) + 1
        best_model = self.get_model(best_num_topics)
        pprint(best_model.print_topics())
        self.save_topic_model(best_model)
        self.plot_coherence_scores(coherence_scores)
        return best_model

    def divide_into_clusters(self, best_model):
        topic_clusters = self.extract_dominant_topics(best_model)
        extended_df = pd.DataFrame(list(zip(list(self.__df["description"]),
                                            topic_clusters)),
                                   columns=['description', 'topic'])
        self.extract_word2vec_models(extended_df)

    @abstractmethod
    def get_model(self, num_topics):
        pass

    @abstractmethod
    def save_topic_model(self, model):
        pass

    @abstractmethod
    def plot_coherence_scores(self, coherence_scores):
        pass

    @abstractmethod
    def extract_dominant_topics(self, best_model):
        pass

    @abstractmethod
    def extract_word2vec_models(self, extended_df):
        pass


class LSA(TopicModel):

    def __init__(self, dataset, folder_path):
        super().__init__(dataset, folder_path)
        self.__lsa_path = self.__folder_path + 'lsa/'

    def get_model(self, num_topics):
        lsa_model = gensim.models.LsiModel(self.__corpus_tfidf,
                                           num_topics=num_topics,
                                           id2word=self.__dictionary)
        return lsa_model

    def save_topic_model(self, model):
        model.save(self.__lsa_path + 'model/LSA.model')

    def plot_coherence_scores(self, coherence_scores):
        figure_path = self.__lsa_path + '../lsa_coherence.png'
        save_coherence_plot(self.__max_num_topics, coherence_scores, figure_path)

    def extract_dominant_topics(self, best_model):
        topic_clusters = []
        for i in range(len(self.__corpus_tfidf)):
            topic_distribution = dict(best_model[self.__corpus_tfidf[i]])
            dominant_topic = max(topic_distribution, key=topic_distribution.get)
            topic_clusters.append(dominant_topic)
        return topic_clusters

    def extract_word2vec_models(self, df):
        distribution_plot_path = self.__lsa_path + 'topic_distribution.png'
        plot_distribution(df, distribution_plot_path, 'topic')
        count = 0
        word2vec_models_path = self.__lsa_path + 'word2vec_models/'
        for category, df_category in df.groupby('topic'):
            count += 1
            model_name = word2vec_models_path + str(count) + ".model"
            word2vec_trainer(df=df_category, size=60, model_path=model_name)


class LDA(TopicModel):
    def __init__(self, dataset, folder_path):
        super().__init__(dataset, folder_path)
        self.__lda_path = self.__folder_path + 'lda/'

    def get_model(self, num_topics):
        lda_model = gensim.models.LdaMulticore(self.__corpus_tfidf,
                                               num_topics=num_topics,
                                               id2word=self.__dictionary,
                                               passes=10, workers=10, iterations=100)
        return lda_model

    def save_topic_model(self, model):
        model.save(self.__lda_path + 'model/LDA.model')

    def plot_coherence_scores(self, coherence_scores):
        figure_path = self.__lda_path + '../lda_coherence.png'
        save_coherence_plot(self.__max_num_topics, coherence_scores, figure_path)

    def extract_dominant_topics(self, best_model):
        topic_clusters = []
        for i in range(len(self.__corpus_tfidf)):
            topic_distribution = dict(best_model[self.__corpus_tfidf[i]])
            dominant_topic = max(topic_distribution, key=topic_distribution.get)
            topic_clusters.append(dominant_topic)
        return topic_clusters

    def extract_word2vec_models(self, df):
        distribution_plot_path = self.__lda_path + 'topic_distribution.png'
        plot_distribution(df, distribution_plot_path, 'topic')
        count = 0
        word2vec_models_path = self.__lda_path + 'word2vec_models/'
        for category, df_category in df.groupby('topic'):
            count += 1
            model_name = word2vec_models_path + str(count) + ".model"
            word2vec_trainer(df=df_category, size=60, model_path=model_name)


def save_coherence_plot(max_num_topics, coherence_scores, figure_path):
    x = [i + 1 for i in range(max_num_topics)]
    plt.figure(figsize=(10, 5))
    plt.plot(x, coherence_scores)
    plt.xticks(np.arange(min(x), max(x) + 1, 1.0))
    plt.xlabel('Number of topics')
    plt.ylabel('Coherence score')
    plt.tight_layout()
    plt.savefig(figure_path)
    plt.show()


def main():
    conf = toml.load('../config-temp.toml')
    topic_modeling_path = '../' + conf['topic_modeling_path']
    df = pd.read_csv('../' + conf["preprocessed_data_path"])
    texts = list(df["description"])

    lsa_obj = LSA(texts, topic_modeling_path)
    best_lsa_model = lsa_obj.search_num_of_topics()
    lsa_obj.divide_into_clusters(best_lsa_model)

    lsa_obj = LDA(texts, topic_modeling_path)
    best_lda_model = lsa_obj.search_num_of_topics()
    lsa_obj.divide_into_clusters(best_lda_model)


if __name__ == "__main__":
    main()
