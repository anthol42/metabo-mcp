import numpy as np
import pandas as pd
from typing import Optional, Tuple
from sklearn.model_selection import train_test_split
from .split import Split


class Spliter:
    def __init__(self,
                 test_ratio: float = 0.2,
                 num_splits: int = 20,
                 max_proportion_diff: Optional[float] = None):
        """
        :param test_ratio: The ratio of the test dataset size to the total dataset size. [0-1]
        :param num_splits: The number of different independent train/test splits to generate.
        :param max_proportion_diff: The maximum prior distribution difference between two classes in the training
        dataset. This means that if it is set to 0.2, if the 0 class correspond to 70% of the training dataset, it will
        be down sample to correspond to a maximum of 60% so that 60% - 40% <= 20% (0.2). If None, no down sampling is
        applied.
        """
        self.test_ratio = test_ratio
        self.num_splits = num_splits
        self.max_proportion_diff = max_proportion_diff


    def split(self, X: pd.DataFrame, y: pd.Series, pairing_column: Optional[str] = None):
        """
        Split the dataset multiple times into training and test sets.
        :param X: The feature dataset as a DataFrame.
        :param y: The target series as a Series.
        :param pairing_column: If you have paired samples, they must not be spread across the train and test. This is
        why you must pass it here. It is the name of the column in the metadata that contains the pairing information.
        :return:
        """

        if pairing_column is not None:
            splits = self._pair_split(X, y, pairing_column)
        else:
            splits = self._split(X, y)

        return splits

    def _pair_split(self, X: pd.DataFrame, y: pd.Series, pairing_column: str) -> list[Split]:
        """
        Split the dataset into training and test sets multiple times, ensuring that paired samples are not split.
        :param X: The feature dataset as a DataFrame.
        :param y: The target series as a Series.
        :param pairing_column: The name of the column in the metadata that contains the pairing information.
        :return: A list of tuples containing the Split object
        """
        splits = []
        unique_pairs = X[pairing_column].unique()

        # Get ys for each pair
        pair_to_y = [y[X[pairing_column] == pair].unique() for pair in unique_pairs]
        assert all(len(y_values) == 1 for y_values in pair_to_y), "Each pair must have a single unique label. Got multiple label for some pairs."
        for _ in range(self.num_splits):
            train_idx, test_idx = train_test_split(unique_pairs, test_size=self.test_ratio, stratify=[y_values[0] for y_values in pair_to_y])
            X_train, X_test = X.loc[X[pairing_column].isin(train_idx)], X[X[pairing_column].isin(test_idx)]
            y_train, y_test = y.loc[X[pairing_column].isin(train_idx)], y[X[pairing_column].isin(test_idx)]
            if self.max_proportion_diff is not None:
                X_train, y_train = self._redistribute(X_train, y_train)
            splits.append(Split(X_train, y_train, X_test, y_test))
        return splits

    def _split(self, X: pd.DataFrame, y: pd.Series) -> list[Split]:
        """
        Split the dataset into training and test sets multiple times.
        :param X: The feature dataset as a DataFrame.
        :param y: The target series as a Series.
        :return: A list of tuples containing the Split object
        """
        splits = []
        for _ in range(self.num_splits):
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=self.test_ratio, stratify=y)
            if self.max_proportion_diff is not None:
                X_train, y_train = self._redistribute(X_train, y_train)
            splits.append(Split(X_train, y_train, X_test, y_test))
        return splits

    def _redistribute(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.DataFrame]:
        # Down sample the training set to respect the max_proportion_diff
        class_counts = y.value_counts(normalize=True)
        min_proportion = class_counts.min()
        max_proportion = class_counts.max()
        if max_proportion - min_proportion > self.max_proportion_diff:
            # Down sample the majority class
            majority_class = class_counts.idxmax()
            minority_class = class_counts.idxmin()
            majority_count = int(
                (min_proportion * (self.max_proportion_diff + 1) / (1 - self.max_proportion_diff)) * len(X))
            X_majority = X[y == majority_class].sample(n=majority_count)
            y_majority = y.loc[X_majority.index]
            X = pd.concat([X_majority, X[y == minority_class]])
            y = pd.concat([y_majority, y[y == minority_class]])

            # Shuffle the training set
            indices = np.arange(len(y))
            np.random.shuffle(indices)
            X = X.iloc[indices]
            y = y.iloc[indices]

        return X, y
