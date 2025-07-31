from pprint import pprint
import pickle
import matplotlib.pyplot as plt
import pandas as pd
from utils import build_report, save_fig
from data import Dataloader, Imputer
from split import Spliter
from optim import Optimizer, ParamRange
from results import plot_confusion_matrix, feature_logplot, feature_heatmap, plot_performances, make_feat_imp, get_important_features_df
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from pyscm import SetCoveringMachineClassifier
from randomscm import RandomScmClassifier
from typing import Tuple, Dict, List

algogrids = [
    (RandomForestClassifier, {
        'n_estimators': ParamRange(10, 250, integer=True),
        'max_depth': ParamRange(2, 20, integer=True),
        'max_features': ParamRange(0.05, 1.),
    }),
    (DecisionTreeClassifier, {
        'criterion': ParamRange(discrete_values=['gini', 'entropy']),
        'max_depth': ParamRange(3, 20, integer=True),
        'min_samples_leaf': ParamRange(2, 20, integer=True),
    }),
    (RandomScmClassifier, {
        'n_estimators': ParamRange(10, 250, integer=True),
        'max_rules': ParamRange(2, 30, integer=True),
        'max_features': ParamRange(0.05, 1.),
    }),
    (SetCoveringMachineClassifier, {
        "model_type": ParamRange(discrete_values=["conjunction", "disjunction"]),
        "max_rules": ParamRange(2, 30, integer=True),
    })
]
if __name__ == '__main__':
    dataloader = Dataloader(
        data_path='.cache/ST002260_data.csv',
        metadata_path='.cache/ST002260_metadata.csv',
        target_column='Shape',
        id_column='Id',
        index_col=None
    )
    X, y, pairs = dataloader.get_data(dataset_index=0) # Binary so ds_idx changes nothing

    # Impute based on class median
    imputer = Imputer()
    X, y = imputer.impute(X, y)

    splitter = Spliter(num_splits=5, max_proportion_diff=0.2)
    splits = splitter.split(X, y)

    inverse = False
    results: List[Dict[str, Tuple[Optimizer, np.ndarray, np.ndarray, float, float]]] = [] # Optimizers, y_pred, y_test, balanced accuracy
    for i, split in enumerate(splits):
        print(f"Split {i+1}/{len(splits)}")
        X_train, X_test, y_train, y_test = split.X_train, split.X_test, split.y_train, split.y_test
        break
    #     if inverse is None:
    #         # Check if we should inverse positive and negative
    #         inverse = input(f'The current labels are: [0: {split.targets[0]}, 1: {split.targets[1]}]. Do you want to inverse them? (y/n): ').lower() == 'y'
    #
    #     if inverse:
    #         y_train = 1 - y_train
    #         y_test = 1 - y_test
    #
    #     results.append({})
    #     for algo_cls, params in algogrids:
    #         print("\tTraining with algorithm:", algo_cls.__name__)
    #         # Create the optimizer
    #         optim = Optimizer(
    #             model_cls=algo_cls,
    #             n=50,
    #             cv=5,
    #             param_grid=params
    #         )
    #         optim.fit(X_train, y_train)
    #         print(optim.score(X_test, y_test))
    #         results[i][algo_cls.__name__] = (
    #             optim,
    #             optim.model.predict(X_test),
    #             y_test,
    #             optim.score(X_train, y_train),
    #             optim.score(X_test, y_test),
    #         )
    # with open('tmp_results.pkl', 'wb') as f:
    #     pickle.dump(results, f)
    with open('tmp_results.pkl', 'rb') as f:
        results = pickle.load(f)
    # Show performances
    plot_performances(results)
    perf = save_fig()
    models = results[0].keys()
    preds = {model: [item[model][1] for item in results] for model in models}
    targets = {model: [item[model][2] for item in results] for model in models}
    cms = []
    for model in models:
        labels = split.targets[::-1] if inverse else split.targets
        plot_confusion_matrix(preds[model], targets[model], labels=labels, model_name=model)
        cms.append(save_fig())

    # Show feature importance
    optimizers = {model: [item[model][0] for item in results] for model in models}
    feature_importances = make_feat_imp(optimizers, split.features)

    feature_heatmap(feature_importances, 5)
    hm = save_fig()
    feature_logplot(feature_importances, 10)
    logplot = save_fig()
    df = get_important_features_df(feature_importances, top_n=10)

    data_info = f"Number of samples: {len(X)}\n\nNumber of features: {X.shape[1]}\n\n"
    build_report([perf, *cms, hm, logplot], df, output_path="tmp.pdf", additional_info=data_info)


