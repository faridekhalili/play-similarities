import gensim.models.keyedvectors as word2vec

if __name__ == '__main__':
    model_path = 'output/word2vec_samples2.model'
    model = word2vec.KeyedVectors.load(model_path)
    score = model.similarity('input', 'value')
    print(score)

