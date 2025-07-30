from typing import Optional, Tuple, List, Dict
from mcp.server.fastmcp import Image, FastMCP, Context
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt

from data import Dataloader, Imputer
from split import Spliter
from optim import Optimizer, ParamRange
from results import plot_confusion_matrix, feature_logplot, feature_heatmap, plot_performances, make_feat_imp, get_important_features_df


from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from pyscm import SetCoveringMachineClassifier
from randomscm import RandomScmClassifier

mcp = FastMCP("MetaboAnalysis")


def save_fig():
    """
    Save the current matplotlib figure to PNG bytes and return the bytes.

    Returns:
        bytes: PNG image data as bytes
    """
    # Create a BytesIO buffer to hold the image data
    buffer = BytesIO()

    # Save the current figure to the buffer in PNG format
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)

    # Get the bytes from the buffer
    buffer.seek(0)  # Reset buffer position to beginning
    png_bytes = buffer.getvalue()

    # Close the buffer to free memory
    buffer.close()
    plt.close()

    return png_bytes


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

@mcp.tool()
async def get_dataframe_info(path: str) -> str:
    """
    Get information about a dataframe stored in a file. The file must be in CSV format.
    It retrieve:
    - Column names
    - Number of rows
    :param path: The path to the CSV file.
    :return: The information (column names and number of rows)
    """
    df = pd.read_csv(path)
    column_names = df.columns.tolist()
    num_rows = len(df)
    info = f'DataFrame Information:\n' \
              f'Column Names: {", ".join(column_names)}\n' \
              f'Number of Rows: {num_rows}'
    return str(info)

@mcp.tool()
async def analysis_pipeline(
        ctx: Context,
        data_path: str,
        metadata_path: str,
        target_column: str,
        id_column: str,
        index_col: Optional[int] = None,
        num_search: int = 100,
        cv: int = 5
) -> Tuple[str, Image, ...]:
    """
    Run a pipeline of auto ML that will preprocess the data, split it and do a hyper parameter search using bayesian
    optimization of multiple interpretable models. Then, the performance and feature importance are reported for
    further analysis.

    The input of the pipeline is a combination of two csv files. The first one is the data file. This one contains the
    features (metabolite[columns] and their quantities[rows]). The second one is the metadata file. This one contains
    information about the samples. The target column is chosen from this metadata file. The id column is used to
    associate the samples in the data file with the metadata file. The index_col is used to specify the index column
    of the files. (They must have the same index column). It is preferable to use the `get_dataframe_info` tool to
    know what column names to put in the parameters.

    The pipeline will make 10 random split of train-test to asser that the found features are not split-dependent. This
    can be understand as a classic machine learning pipeline that is run 10 times with different random train-test
    splits. The hyperparameters of each models are optimized using Bayesian optimization with cross validation
    (Only on the train set of the split). Then, the scores are the balanced accuracy as some datasets are highly
    imbalanced.

    Multiple figures are reported:
    - A performance barplot (Balanced accuracy of each model on the train and test sets) [The error bars are the standard deviation of the balanced accuracy across the splits]
    - A confusion matrix for each model [Agglomerated across the splits]
    - A feature importance heatmap. The columns are the model and the features are the rows. The cells are colored by the importance of the feature for the model. [Aggregated across the splits]
    - A feature logplot. The x-axis is the feature and the y-axis is the importance of the feature for ALL models. [Aggregated across the splits]
    - A feature importance table as csv

    NOTE: The pipeline currently only supports binary classification problems.

    :param data_path: The path to the data file (CSV) containing the features.
    :param metadata_path: The path to the metadata file (CSV).
    :param target_column: The column in the metadata file that contains the target variable (the label to predict).
    :param id_column: The column in the metadata and data file that associates the samples.
    :param index_col: If any, the column index of the dataframe index.
    :param num_search: The number of bayesian optimization search iterations to perform. Default is 100.
    :param cv: The number of cross-validation folds to use for the hyperparameter search. Default is 5.
    :return: The results (figures and feature importance table) of the analysis pipeline.
    """

    dataloader = Dataloader(
        data_path=data_path,
        metadata_path=metadata_path,
        target_column=target_column,
        id_column=id_column,
        index_col=index_col
    )
    X, y, pairs = dataloader.get_data(dataset_index=0) # Binary so ds_idx changes nothing

    # Impute based on class median
    imputer = Imputer()
    X, y = imputer.impute(X, y)

    splitter = Spliter(num_splits=10, max_proportion_diff=0.2)
    splits = splitter.split(X, y)

    inverse = False # Since sampling is not supported in claude desktop, we disable this for now
    results: List[Dict[str, Tuple[Optimizer, np.ndarray, np.ndarray, float, float]]] = [] # Optimizers, y_pred, y_test, balanced accuracy
    for i, split in enumerate(splits):
        await ctx.info(f"Split {i+1}/{len(splits)}")
        X_train, X_test, y_train, y_test = split.X_train, split.X_test, split.y_train, split.y_test

        if inverse is None:
            # Check if we should inverse positive and negative
            inverse = input(f'The current labels are: [0: {split.targets[0]}, 1: {split.targets[1]}]. Do you want to inverse them? (y/n): ').lower() == 'y'

        if inverse:
            y_train = 1 - y_train
            y_test = 1 - y_test

        results.append({})
        for algo_cls, params in algogrids:
            await ctx.info("Training with algorithm: {algo_cls.__name__}")
            # Create the optimizer
            optim = Optimizer(
                model_cls=algo_cls,
                n=num_search,
                cv=cv,
                param_grid=params
            )
            optim.fit(X_train, y_train, logger=ctx.info)
            await ctx.info(str(optim.score(X_test, y_test)))
            results[i][algo_cls.__name__] = (
                optim,
                optim.model.predict(X_test),
                y_test,
                optim.score(X_train, y_train),
                optim.score(X_test, y_test),
            )
    # Show performances
    plot_performances(results)
    performances = Image(data=save_fig(), format="image/png")

    models = results[0].keys()
    preds = {model: [item[model][1] for item in results] for model in models}
    targets = {model: [item[model][2] for item in results] for model in models}
    confusion_matrices = []
    for model in models:
        labels = split.targets[::-1] if inverse else split.targets
        plot_confusion_matrix(preds[model], targets[model], labels=labels, model_name=model)
        confusion_matrices.append(Image(data=save_fig(), format="image/png"))


    # Show feature importance
    optimizers = {model: [item[model][0] for item in results] for model in models}
    feature_importances = make_feat_imp(optimizers, split.features)

    feature_heatmap(feature_importances, 5)
    feat_hm = Image(data=save_fig(), format="image/png")

    feature_logplot(feature_importances, 10)
    logplot = Image(data=save_fig(), format="image/png")

    feat_imp = get_important_features_df(feature_importances, top_n=10).to_csv(index=None)

    return (
        feat_imp,
        performances,
        *confusion_matrices,
        feat_hm,
        logplot
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")
