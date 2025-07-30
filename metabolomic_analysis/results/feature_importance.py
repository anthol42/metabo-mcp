import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict
import seaborn as sns

def get_feat_imp_scm(rules, rule_imp, num_features):
    feat = [stump.feature_idx for stump in rules]
    feat_imp = np.zeros(num_features)
    for idx, imp in zip(feat, rule_imp):
        feat_imp[idx] = imp

    return feat_imp

def make_feat_imp(optimizers: Dict[str, 'Optimizer'], feature_names: list[str]) -> Dict[str, pd.DataFrame]:
    feature_importances = {}
    for name, optimizer in optimizers.items():
        if name == "SetCoveringMachineClassifier":
            feats = [get_feat_imp_scm(optim.model.model_.rules, optim.model.rule_importances_, len(feature_names)) for optim
                     in optimizer]
        else:
            feats = [optim.model.feature_importances_ for optim in optimizer]

        # Normalize the feature importances
        feats = [feat / np.sum(feat) for feat in feats]

        # Agglomerate the feature importances using the mean
        feats = np.mean(feats, axis=0)

        # Normalize again
        feats = feats / np.sum(feats)

        # Make a dataframe
        feat_imp_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feats
        }).sort_values(by='importance', ascending=False)

        feature_importances[name] = feat_imp_df

    return feature_importances
def feature_heatmap(feature_importance: Dict[str, pd.DataFrame], top_n: int = 10):
    """
    Plot a kinda heatmap of the feature importance for each model for the top n features.
    :param feature_importance: A dictionary where keys are model names and values are DataFrames with feature
    importance. The DataFrame should have a column 'feature' with feature names and a column 'importance' with their
    importance scores.
    :param top_n: The top n features to sample in each model. If model do not chooses the same features. the figure
    will contain more than top_n features.
    :return: None
    """

    # Get top features for each model
    all_top_features = set()
    model_top_features = {}

    for model_name, df in feature_importance.items():
        # Sort by importance and get top_n features
        top_features = df.nlargest(top_n, 'importance')
        # Renormalize the top_features so that the sum to 1
        top_features['importance'] = top_features['importance'] / top_features['importance'].sum()
        model_top_features[model_name] = top_features
        all_top_features.update(top_features['feature'].tolist())

    # Create a matrix for the heatmap
    features_list = sorted(list(all_top_features), key=lambda x: sum([
        model_top_features[model]['importance'].loc[model_top_features[model]['feature'] == x].item()
        if x in model_top_features[model]['feature'].values else 0
        for model in feature_importance.keys()
    ]), reverse=True)

    models_list = list(feature_importance.keys())

    # Create the importance matrix
    importance_matrix = np.zeros((len(features_list), len(models_list)))

    for i, feature in enumerate(features_list):
        for j, model in enumerate(models_list):
            model_df = model_top_features[model]
            if feature in model_df['feature'].values:
                importance_matrix[i, j] = model_df[model_df['feature'] == feature]['importance'].values[0]
            else:
                importance_matrix[i, j] = 0

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, len(features_list) * 0.4))

    # Create heatmap
    im = ax.imshow(importance_matrix, cmap='Blues', aspect='auto')

    # Set ticks and labels
    ax.set_xticks(range(len(models_list)))
    ax.set_xticklabels(models_list)
    ax.set_yticks(range(len(features_list)))
    ax.set_yticklabels(features_list)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Importance', rotation=270, labelpad=15)

    # Set title
    ax.set_title(f'Agglomerated top {top_n} features for all splits', fontsize=14, pad=20)

    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    # Adjust layout
    plt.tight_layout()


def feature_logplot(feature_importance: Dict[str, pd.DataFrame], top_n: int = 10, figsize: tuple = None):
    """
    Make a horizontal bar plot of the top_n most important features across all models.
    It normalizes its importance in percentage and plot them in log2 scale.
    :param feature_importance: A dictionary where keys are model names and values are DataFrames with feature
    importance. The DataFrame should have a column 'feature' with feature names and a column 'importance' with their
    importance scores.
    :param top_n: The top n features to sample in each model. Then, the top n remaining features are plot. This is done
    in a 2 step filtering.
    :param figsize: The size of the figure to plot. If None, the default size is used.
    :return: None
    """

    # Step 1: Sample the top_n features from each model
    all_top_features = set()
    model_top_features = {}

    for model_name, df in feature_importance.items():
        # Sort by importance and get top_n features
        top_features = df.nlargest(top_n, 'importance')
        # Renormalize the top_features so that the sum to 1
        top_features['importance'] = top_features['importance'] / top_features['importance'].sum()
        model_top_features[model_name] = top_features
        all_top_features.update(top_features['feature'].tolist())

    # Step 2: Agglomerate all top features dataset by summing their importance
    all_features_df = pd.DataFrame(columns=['feature', 'importance'])
    for model_name, df in model_top_features.items():
        all_features_df = pd.concat([all_features_df, df], ignore_index=True)
    all_features_df = all_features_df.groupby('feature', as_index=False).sum()

    # Step 3: Sample the top_n features from the agglomerated dataset
    all_features_df = all_features_df.nlargest(top_n, 'importance')
    all_features_df['importance'] = all_features_df['importance'] / all_features_df['importance'].sum()

    # Step 4: Plot the features in log2 scale
    figsize and plt.figure(figsize=figsize)
    ax = sns.barplot(x='importance', y='feature', data=all_features_df)

    # Add value labels at the left of each bar
    med_imp = np.median(all_features_df['importance'].values)
    for i, (idx, row) in enumerate(all_features_df.iterrows()):
        # Get the bar width (importance value)
        bar_width = row['importance']
        # Position the text slightly to the left of the bar start
        x = bar_width if bar_width >= med_imp else bar_width + 0.02
        ax.text(x, i, f'{100*bar_width:.1f}%',
                va='center', ha='right',
                color='black', fontsize=10)

    plt.xscale('log', base=2)
    plt.xlim(None, all_features_df['importance'].max() * 1.1)
    plt.xticks(ticks=[], labels=[])
    plt.xlabel('Importance')
    plt.ylabel('Feature')
    plt.title(f'Top {top_n} features across all models', fontsize=14, pad=20)
    plt.tight_layout()

# Example usage:
if __name__ == "__main__":
    # Example data structure
    sample_data = {
        'DecisionTree': pd.DataFrame({
            'feature': ['caffeine', 'glucose', 'fructose'],
            'importance': [0.95, 0.87, 0.76]
        }),
        'RandomForest': pd.DataFrame({
            'feature': ['caffeine', 'TG', 'aspartic acid'],
            'importance': [0.92, 0.85, 0.73]
        }),
        'SCM': pd.DataFrame({
            'feature': ['glucose', 'D-Alanine', 'fructose'],
            'importance': [0.88, 0.71, 0.68]
        }),
        'RandomSCM': pd.DataFrame({
            'feature': ['L-Glycine', 'caffeine', 'cortisol'],
            'importance': [0.90, 0.65, 0.62]
        })
    }

    # Call the function
    feature_logplot(sample_data, top_n=3)