import pandas as pd
from typing import Optional, Any, Tuple, Dict, List


class Dataloader:
    def __init__(self, data_path: str, metadata_path: str,
                 feature_columns: Optional[list[str]] = None,
                 target_column: Optional[str] = None,
                 id_column: Optional[str] = None,
                 pairing_column: Optional[str] = None,
                 subset: Optional[dict[str, list[str]]] = None,
                 index_col: Optional[int] = None):
        """
        Initialize the Dataloader with paths to data and metadata files.
        :param data_path: The path to the data file (CSV format).
        :param metadata_path: The path to the metadata file (CSV format).
        :param feature_columns: List of column names in the metadata file that represent features. All features in the
        data file are used. By default, no columns in the metadata file are considered as features.
        :param target_column: The name of the target column. We currently only support binary classification. This
        means that if multiple conditions are present in the target column, the data will be automatically split by
        pairs of conditions. A maximum of 10 conditions is allowed. If not set during initialization, the target column
        must be set before calling the `get_data` method.
        :param id_column: The name of the column in the metadata file that contains the ID which is associated to
        the index of the data file. If not set, the ID column must be set before calling the `get_data` method.
        :param subset: A dictionary to filter the data based on specific conditions. The keys are column names and the
        values are the possible values the column can take. If None, no filtering is applied.
        :param index_col: The index of the column in the csv file for the data and metadata files.
        """
        self.data_path = data_path
        self.metadata_path = metadata_path
        self.data = self._load_data(index_col=index_col)
        self.metadata = self._load_metadata(index_col=index_col)
        self.feature_columns = feature_columns
        self.set_target_column(target_column)
        self.set_id_column(id_column)
        self.pairing_column = pairing_column
        self.subset = subset

    def set_target_column(self, target_column: Optional[str]):
        if target_column is None:
            return
        if target_column not in self.metadata.columns:
            raise ValueError(f'Target column {target_column} not found in metadata file')
        self.target_column = target_column

    def set_id_column(self, id_column: Optional[str]):
        if id_column is not None and id_column not in self.metadata.columns:
                raise ValueError(f'ID column {id_column} not found in metadata file')
        self.id_column = id_column

    def get_data(self, dataset_index: int = 0) -> Tuple[pd.DataFrame, pd.Series, Optional[List[Tuple[str, str]]]]:
        """
        Prepare the dataset for analysis.
        :param dataset_index: The index of the dataset to prepare in case the label is not binary
        :return: The full feature dataset as a DataFrame and the target variable as a Series. It also returns the list
        of target pairs when the target variable is not binary.
        """
        if self.target_column is None:
            raise RuntimeError(f'Target column is not set. Please set it before calling get_data()')
        if self.id_column is None:
            raise RuntimeError(f'ID column is not set. Please set it before calling get_data()')

        # Filter the metadata based on the subset if provided
        metadata = self._filter_data(self.metadata, self.subset)
        data = pd.merge(self.data.reset_index(), metadata, left_on=self.id_column, right_on=self.id_column, how='right')
        data = data.set_index(self.id_column)

        features = list(self.data.columns) + (self.feature_columns or [])
        features.pop(features.index(self.id_column))
        targets = data[self.target_column]
        data = data[features]

        # Now, split in pairs
        if len(targets.unique()) > 2:
            unique_targets = targets.unique()
            if len(unique_targets) > 10:
                raise ValueError('More than 10 unique conditions found in target column. '
                                 'Please reduce the number of conditions.')
            pairs = [(unique_targets[i], unique_targets[j]) for i in range(len(unique_targets))
                 for j in range(i + 1, len(unique_targets))]
            if dataset_index >= len(pairs):
                raise IndexError(f'Dataset index {dataset_index} out of range for available pairs.')
            target_pair = pairs[dataset_index]
            data = data[targets.isin(target_pair)]
            targets = targets[targets.isin(target_pair)]
        else:
            pairs = None
        return data, targets, pairs

    @staticmethod
    def _filter_data(metadata: pd.DataFrame, subset: Dict[str, list[str]]) -> pd.DataFrame:
        if subset is None:
            return metadata
        for column, values in subset.items():
            if column not in metadata.columns:
                raise ValueError(f'Column {column} not found in metadata file')
            metadata = metadata.loc[metadata[column].isin(values)]

        return metadata
    def _load_data(self, index_col: Optional[int]) -> pd.DataFrame:
        """
        Load the data from the specified CSV file. It automatically detects the separator and encodings.
        :return: The dataframe
        """
        data = pd.read_csv(self.data_path, sep=None, engine='python', index_col=index_col)
        return data

    def _load_metadata(self, index_col: Optional[int]) -> pd.DataFrame:
        """
        Load the metadata from the specified CSV file. It automatically detects the separator and encodings.
        :return: The dataframe
        """
        metadata = pd.read_csv(self.metadata_path, sep=None, engine='python', index_col=index_col)
        return metadata

if __name__ == '__main__':
    # Example usage
    dataloader = Dataloader(
        data_path='../.cache/MTBLS28_CombinedData2_forML.csv',
        metadata_path='../.cache/s_MTBLS28_merged.csv',
        target_column='Factor Value[Smoking]',
        id_column='Sample_Name'
    )

    data, targets, pairs = dataloader.get_data(dataset_index=1)
    print(data)
    print(targets)
    print(pairs)