import pandas as pd


class Split:
    def __init__(self, X_train: pd.DataFrame, y_train: pd.Series,
                 X_test: pd.DataFrame, y_test: pd.Series):
        """
        Initialize the Split object with the feature dataset and target series.
        :param X_train: The feature dataset as a DataFrame.
        :param y_train: The target series as a Series for the training set.
        :param X_test: The feature dataset as a DataFrame for the test set.
        :param y_test: The target series as a Series for the test set.
        """
        self.features = X_train.columns
        self.train_index = X_train.index
        self.test_index = X_test.index

        self.X_train = X_train.to_numpy()
        self.X_test = X_test.to_numpy()

        self.targets = sorted(list(y_train.unique()))
        self.y_train = y_train.map(lambda x: self.targets.index(x)).to_numpy()
        self.y_test = y_test.map(lambda x: self.targets.index(x)).to_numpy()
