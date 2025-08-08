from typing import Optional, Dict, Any, Tuple, List, Callable
import numpy as np
import multiprocessing as mp
import optuna
import uuid
import tempfile
import os
from sklearn.metrics import balanced_accuracy_score
import time
import sys
import signal

class ParamRange:
    def __init__(self, min_value: Any = None, max_value: Any = None , discrete_values: Optional[List] = None,
                 log: bool = False, integer: bool = False):
        min_v = min_value is None
        max_v = max_value is None
        dis_v = discrete_values is None
        if any([min_v, max_v]) and not all([min_v, max_v]):
            raise ValueError("Either both min_value and max_value must be set, or neither.")
        if any([min_v, max_v]) and dis_v:
            raise ValueError("If min_value and max_value are set, discrete_values must not be None.")
        if all([min_v, max_v]) and dis_v:
            raise ValueError("min_value and max_value or discrete_values must be set, got all None")

        self.min_value = min_value
        self.max_value = max_value
        self.discrete_values = discrete_values
        self.log = log
        self.integer = integer

    def __repr__(self):
        if self.min_value is None:
            return f"ParamRange({self.discrete_values}, log={self.log})"
        else:
            return f"ParamRange(min_value={self.min_value}, max_value={self.max_value}, log={self.log})"

def _objective(trial: optuna.Trial, model_cls: type, Xs_train: List[np.ndarray], ys_train: List[np.ndarray],
               Xs_val: List[np.ndarray], ys_val: List[np.ndarray], param_grid: Dict[str, ParamRange]) -> float:
    """
    Objective function for Optuna to optimize the model's hyperparameters. It returns the balanced accuracy score of
    the model.
    :param trial: The trial
    :param model_cls: The model class to optimize.
    :param Xs_train: The training features for each split.
    :param ys_train: The training targets for each split.
    :param Xs_val: The validation features for each split.
    :param ys_val: The validation targets for each split.
    :param param_grid: The parameter grid to optimize.
    :return: The balanced accuracy score of the model using the given hyperparameters.
    """
    hparams = {}
    for param_name, param_range in param_grid.items():
        if param_range.discrete_values is not None:
            hparams[param_name] = trial.suggest_categorical(param_name, param_range.discrete_values)
        else:
            if param_range.integer:
                hparams[param_name] = trial.suggest_int(param_name, param_range.min_value, param_range.max_value, log=param_range.log)
            else:
                hparams[param_name] = trial.suggest_float(param_name, param_range.min_value, param_range.max_value, log=param_range.log)
    scores = []
    for X_train, X_val, y_train, y_val in zip(Xs_train, Xs_val, ys_train, ys_val):
        # Init with hparams
        model = model_cls(**hparams)
        # Train
        model.fit(X_train, y_train)

        # Eval
        y_pred = model.predict(X_val)
        scores.append(balanced_accuracy_score(y_val, y_pred))

    # Return the mean score across all cross validation splits
    return np.mean(scores) - np.std(scores)


def _worker(db_path: str, study_name: str, n: int, model_cls: type, Xs_train: List[np.ndarray], ys_train: List[np.ndarray],
            Xs_val: List[np.ndarray], ys_val: List[np.ndarray], param_grid: Dict[str, ParamRange]) -> Dict[str, Any]:
    """
    Worker that works in its own process to optimize the model using Optuna. It loads the study and optimizes the
    objective function.
    :param db_path: Path to the database where the study is stored.
    :param study_name: Name of the study.
    :param n: The number of trials to run for this worker.
    :param model_cls: The model class to optimize.
    :param Xs_train: The training features for each split.
    :param ys_train: The training targets for each split.
    :param Xs_val: The validation features for each split.
    :param ys_val: The validation targets for each split.
    :param param_grid: The parameter grid to optimize.
    :return: None
    """
    optuna.logging.set_verbosity(optuna.logging.ERROR)
    if len(Xs_train) == 0 or len(Xs_val) == 0 or len(ys_train) == 0 or len(ys_val) == 0:
        raise ValueError("At least one of the training or validation sets is empty. Please check your data.")
    study = optuna.load_study(study_name=study_name, storage=f"sqlite:///{db_path}")

    for i in range(n):
        try:
            study.optimize(lambda trial: _objective(trial, model_cls, Xs_train, ys_train, Xs_val, ys_val, param_grid),
                           n_trials=1, timeout=60 * 60)  # 1 hour timeout
        except Exception as e:
            print(f"Error during optimization: {e}")
            continue

class Optimizer:
    def __init__(self, model_cls: type, n: int, cv: int, param_grid: Dict[str, ParamRange], num_workers: int = -1):
        self.model_cls = model_cls
        self.n = n
        self.cv = cv
        self.param_grid = param_grid
        self.num_workers = num_workers # -1 means use all available cores
        self.model = None

    def fit(self, X: np.ndarray, y: np.ndarray, *, pairing_column_data: Optional[np.ndarray] = None,
            timeout: Optional[int] = None, progress_cb: Optional[Callable[[int], None]] = None, model: Any = None, logger = print) -> None:
        """
        Search for the best hyperparameters using Optuna, then train the model with the best hyperparameters.
        After, the trained model is accessible from the `model` attribute.
        :param X: The feature dataset as a numpy array.
        :param y: The targets as a numpy array.
        :param pairing_column_data: The pairing column data as a numpy array. Each pair must have a single unique int32 id.
        :param timeout: The timeout in seconds for the optimization. If None, no timeout is applied.
        :param progress_cb: A callback function to report progress. It should accept an integer argument representing
        the number of trials completed. If None, no progress is reported.
        :param model: The model to train. If provided, the hyperparameter search will be bypassed and the model will
        be trained with the provided hyperparameters. If None, the model will be optimized using Optuna.
        :return: None
        """
        if model is not None:
            self.model = model
            self.model.fit(X, y)
        else:
            hparams = self.optimize(X, y, pairing_column_data=pairing_column_data, timeout=timeout, progress_cb=progress_cb, logger=logger)
            self.model = self.model_cls(**hparams)
            self.model.fit(X, y)

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Evaluate the trained model on the given dataset using the balanced accuracy score.
        :param X: The feature dataset as a numpy array.
        :param y: The targets as a numpy array.
        :return: The balanced accuracy score of the model on the given dataset.
        """
        if self.model is None:
            raise RuntimeError("Model is not trained yet. Please call `fit` method first.")
        y_pred = self.model.predict(X)
        return balanced_accuracy_score(y, y_pred)

    def optimize(self, X: np.ndarray, y: np.ndarray, *, pairing_column_data: Optional[np.ndarray] = None,
                 timeout: Optional[int] = None, progress_cb: Optional[Callable[[int], None]] = None, logger = print) -> dict:
        """
        Uses Optuna to do a baysian hyperparameter optimization of the model using cross-validation.
        :param X: The feature dataset as a numpy array.
        :param y: The target series as a numpy array.
        :param pairing_column_data: If available, the pairing column data as a numpy array. This is used to ensure that
        paired samples are not split across train and test sets.
        :param timeout: If not None, the timeout parameter is ignored.
        :param progress_cb: A callback function to report progress. It should accept an integer argument representing
        the number of completed trials.
        :return: A dictionary containing the best hyperparameters found during optimization.
        """
        # Split along the pairing column if provided
        if pairing_column_data is None:
            Xs_train, Xs_val, ys_train, ys_val = self._split(X, y)
        else:
            Xs_train, Xs_val, ys_train, ys_val = self._pair_split(X, y, pairing_column_data)

        # Create study
        uuid_val = uuid.uuid4()
        db = f"{uuid_val}.sqlite3"
        temp_dir = tempfile.gettempdir()
        db_path = os.path.abspath(os.path.join(temp_dir, db))
        study_name = f"{self.model_cls.__name__}-{uuid_val}"

        processes = []

        try:
            study = optuna.create_study(direction="maximize",
                                        study_name=study_name,
                                        storage=f"sqlite:///{db_path}",
                                        load_if_exists=True)

            # Launch workers
            num_workers = self.num_workers
            if num_workers == -1:
                num_workers = os.cpu_count() or 1

            # Distribute trials across workers
            trials_per_worker = self.n // num_workers
            remaining_trials = self.n % num_workers

            # def signal_handler(signum, frame):
            #     logger("\nReceived interrupt signal. Terminating processes...")
            #     for process in processes:
            #         if process.is_alive():
            #             process.terminate()
            #     for process in processes:
            #         process.join(timeout=5)  # Give processes 5 seconds to terminate
            #     sys.exit(0)
            #
            # # Register the signal handler
            # signal.signal(signal.SIGINT, signal_handler)
            for i in range(num_workers):
                worker_trials = trials_per_worker + (1 if i < remaining_trials else 0)

                if worker_trials > 0:
                    process = mp.Process(
                        target=_worker,
                        args=(db_path, study_name, worker_trials, self.model_cls,
                              Xs_train, ys_train, Xs_val, ys_val, self.param_grid)
                    )
                    process.start()
                    processes.append(process)

            # Monitor progress if requested
            if progress_cb is not None:
                while any(p.is_alive() for p in processes):
                    time.sleep(5)  # Check every 5 seconds
                    try:
                        current_study = optuna.load_study(study_name=study_name, storage=f"sqlite:///{db_path}")
                        completed_trials = len([trial for trial in current_study.trials if trial.state == optuna.trial.TrialState.COMPLETE])
                        progress_cb(completed_trials)
                    except:
                        pass  # Continue if we can't load study temporarily

            # Wait for all processes to complete
            for process in processes:
                if timeout:
                    process.join(timeout=timeout)
                    if process.is_alive():
                        logger(f"Process timed out, terminating...")
                        process.terminate()
                        process.join()
                else:
                    process.join()

            # Get best configuration from the study
            study = optuna.load_study(study_name=study_name, storage=f"sqlite:///{db_path}")

            if len(study.trials) == 0:
                logger("No trials completed successfully.")
                return {}

            best_params = study.best_params
            best_value = study.best_value

            logger(f"Optimization completed. Best score: {best_value:.4f}")
            logger(f"Best parameters: {best_params}")

            return best_params

        except Exception as e:
            logger(f"Error during optimization: {e}")
            for process in processes:
                if process.is_alive():
                    process.terminate()
            for process in processes:
                process.join(timeout=5)
            return {}

        finally:
            # Ensure all processes are terminated
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join()

            # Clean up: Delete study database
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
            except Exception as e:
                logger(f"Warning: Could not delete temporary database {db_path}: {e}")


    def _split(self, X: np.ndarray, y: np.ndarray) -> Tuple[
                                                            List[np.ndarray],
                                                            List[np.ndarray],
                                                            List[np.ndarray],
                                                            List[np.ndarray]
                                                            ]:
        """
        Split the dataset into training and test sets multiple times in a cross validation fashion.
        :param X: The feature dataset as a numpy array.
        :param y: The target series as a numpy array.
        :return: A tuple containing the training features and targets.
        """
        Xs_train, Xs_val, ys_train, ys_val = [], [], [], []

        # Cross validation split
        indexes = np.arange(len(X))
        np.random.shuffle(indexes)

        fold_size = len(X) // self.cv
        for i in range(self.cv):
            test_indexes = indexes[fold_size * i:fold_size * (i + 1)]
            train_mask  = np.ones(len(X), dtype=bool)
            train_mask[test_indexes] = False
            X_train = X[train_mask]
            X_val = X[test_indexes]
            y_train = y[train_mask]
            y_val = y[test_indexes]

            Xs_train.append(X_train)
            Xs_val.append(X_val)
            ys_train.append(y_train)
            ys_val.append(y_val)

        return Xs_train, Xs_val, ys_train, ys_val

    def _pair_split(self, X: np.ndarray, y: np.ndarray, pairs: np.ndarray[np.int32]) -> Tuple[
                                                            List[np.ndarray],
                                                            List[np.ndarray],
                                                            List[np.ndarray],
                                                            List[np.ndarray]
                                                            ]:
        """
        Split the dataset into training and test sets multiple times, ensuring that paired samples are not split.
        :param X: The feature dataset as a numpy array.
        :param y: The targets as a numpy array.
        :param pairs: The pairing column data as a numpy array. Each pair must have a single unique int32 id.
        :return: The splits
        """
        Xs_train, Xs_val, ys_train, ys_val = [], [], [], []
        unique_pairs = np.unique(pairs)

        # Verify that each pair has a single unique label
        pair_to_y = [np.unique(y[pairs == pair]) for pair in unique_pairs]
        assert all(len(y_values) == 1 for y_values in pair_to_y), "Each pair must have a single unique label. Got multiple labels for some pairs."

        np.random.shuffle(unique_pairs)
        fold_size = len(unique_pairs) // self.cv
        for i in range(self.cv):
            test_idx = unique_pairs[fold_size * i:fold_size * (i + 1)]
            train_idx = unique_pairs[~np.isin(unique_pairs, test_idx)]
            X_train = X[np.isin(pairs, train_idx)]
            X_val = X[np.isin(pairs, test_idx)]
            y_train = y[np.isin(pairs, train_idx)]
            y_val = y[np.isin(pairs, test_idx)]

            Xs_train.append(X_train)
            Xs_val.append(X_val)
            ys_train.append(y_train)
            ys_val.append(y_val)

        return Xs_train, Xs_val, ys_train, ys_val