import pandas as pd
from typing import Literal
class Imputer:
    def __init__(self, method: Literal['median'] = 'median'):
        self.method = method


    def impute(self, X: pd.DataFrame, y: pd.Series):
        """
        Impute missing values by taking the median for each class.
        """
        for col in X.columns[X.isna().any(axis=0).values]:
            for cls in y.unique():
                median = X.loc[y == cls, col].median()
                X.loc[(y == cls) & X[col].isna(), col] = median
        return X, y