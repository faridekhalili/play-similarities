import toml
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nltk.tokenize import word_tokenize
from gensim.models import Word2Vec
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report


def train_and_test_word2vec(df, model_path):
    w2v_vector_size = 60
    plot_path = model_path + '../distribution.png'
    w2v_vectors_path = model_path + 'train_word2vec_vectors.csv'
    cls_report_path = model_path + 'classification_report.csv'

    # Plotting Number of applications per category
    plot_distribution(df, plot_path)

    # Splitting the dataset into train and test for further assessments
    X_train, X_test, Y_train, Y_test = split_train_test(df)

    # Train the word2vec model and save it in the given path.
    word2vec_trainer(X_train, w2v_vector_size, model_path)
    w2v_model = Word2Vec.load(model_path)

    # Writing the vectors achieved from the w2v_model in train_word2vec_vectors.csv.
    write_w2vec_vectors(w2v_vectors_path, X_train, w2v_model, w2v_vector_size)
    # Reading the word2vec vectors into a pandas df.
    w2v_df = pd.read_csv(w2v_vectors_path)

    # Train a classifier given word2vec vectors.
    classifier_model = fit_classifier(w2v_df, Y_train)

    # Test how accurate the results of the classification are based on the w2v_model.
    test_classifier(X_test, Y_test, w2v_model, classifier_model, w2v_vector_size, cls_report_path)


def plot_distribution(df, plot_path):
    plt.figure(figsize=(15, 5))
    pd.value_counts(df['label']).plot.bar(title="category distribution in the dataset")
    plt.xlabel("category")
    plt.ylabel("Number of applications in the dataset")
    plt.savefig(plot_path)


def split_train_test(df, test_size=0.3, shuffle_state=True):
    # Data is distributed for each category proportionately.
    X_train, X_test, Y_train, Y_test = train_test_split(df['description'], df['label'],
                                                        shuffle=shuffle_state,
                                                        test_size=test_size,
                                                        random_state=15)

    X_train = X_train.reset_index()
    X_test = X_test.reset_index()
    Y_train = Y_train.to_frame()
    Y_train = Y_train.reset_index()
    Y_test = Y_test.to_frame()
    Y_test = Y_test.reset_index()
    return X_train, X_test, Y_train, Y_test


def word2vec_trainer(df, size, model_path):
    start_time = time.time()
    model = Word2Vec(list(df["description"]),
                     min_count=1, size=size, workers=3, window=3, sg=1)
    print("Time taken to train the word2vec model: " + str(time.time() - start_time))
    model.save(model_path)


def write_w2vec_vectors(word2vec_filename, df, w2v_model, w2v_vector_size):
    with open(word2vec_filename, 'w+') as word2vec_file:
        for index, row in df.iterrows():
            model_vector = (np.mean([w2v_model[token] for token in row['description']], axis=0)).tolist()
            if index == 0:
                header = ",".join(str(ele) for ele in range(w2v_vector_size))
                word2vec_file.write(header)
                word2vec_file.write("\n")
            # Check if the line exists else it is vector of zeros
            if type(model_vector) is list:
                line1 = ",".join([str(vector_element) for vector_element in model_vector])
            else:
                line1 = ",".join([str(0) for i in range(w2v_vector_size)])
            word2vec_file.write(line1)
            word2vec_file.write('\n')


def fit_classifier(X_df, y_df):
    clf_decision_word2vec = DecisionTreeClassifier()
    start_time = time.time()
    clf_decision_word2vec.fit(X_df, y_df['label'])
    print("Time taken to fit the classifier model with word2vec vectors: " + str(time.time() - start_time))
    return clf_decision_word2vec


def test_classifier(X_test, Y_test, w2v_model, classifier_model, w2v_vector_size, cls_report_path):
    test_features_w2v = []
    for index, row in X_test.iterrows():
        model_vector = np.mean([w2v_model[token] for token in row['description']], axis=0)
        if type(model_vector) is list:
            test_features_w2v.append(model_vector)
        else:
            test_features_w2v.append(np.array([0 for i in range(w2v_vector_size)]))
    test_predictions_w2v = classifier_model.predict(test_features_w2v)
    cls_report = classification_report(classification_report(Y_test['label'], test_predictions_w2v))
    report_df = pd.DataFrame(cls_report).transpose()
    report_df.to_csv(cls_report_path)


def main():
    conf = toml.load('../config-temp.toml')
    df = pd.read_csv('../' + conf["preprocessed_data_path"])
    model_path = '../' + conf['model_path']
    train_and_test_word2vec(df, model_path)


if __name__ == "__main__":
    main()
