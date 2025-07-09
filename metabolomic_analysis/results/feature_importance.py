import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict
import seaborn as sns


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

    # Show the plot
    plt.show()

def feature_logplot(feature_importance: Dict[str, pd.DataFrame], top_n: int = 10):
    pass

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
    feature_heatmap(sample_data, top_n=2)