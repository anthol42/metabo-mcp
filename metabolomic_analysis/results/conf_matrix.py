import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from sklearn.metrics import confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def plot_confusion_matrix(preds: List[np.ndarray], targets: List[np.ndarray], labels: Tuple[str, str]):
    """
    Plot a confusion matrix that is the agglomeration of each confusion matrix of each split. The aggregation used is
    the sum, then the confusion matrix is normalized to get percentage values.
    :param preds: A list of numpy arrays containing the predictions for each split. Each array should be 1D and boolean
    :param targets: A list of numpy arrays containing the targets for each split. Each array should be 1D and boolean
    :param labels: A tuple containing the labels for 0 and 1 classes, e.g. ('Negative', 'Positive')
    :return: None
    """
    if len(preds) != len(targets):
        raise ValueError("Number of prediction arrays must match number of target arrays")

    if len(preds) == 0:
        raise ValueError("At least one prediction/target pair must be provided")

    # Initialize the aggregated confusion matrix
    aggregated_cm = np.zeros((2, 2), dtype=int)

    # Sum confusion matrices from all splits
    for pred, target in zip(preds, targets):
        # Convert to numpy arrays if not already
        pred = np.asarray(pred)
        target = np.asarray(target)

        # Validate input shapes
        if pred.shape != target.shape:
            raise ValueError(
                f"Prediction and target arrays must have the same shape. Got {pred.shape} and {target.shape}")

        if pred.ndim != 1:
            raise ValueError(f"Prediction and target arrays must be 1D. Got {pred.ndim}D array")

        # Ensure binary values (0 or 1)
        if not np.all(np.isin(pred, [0, 1])):
            raise ValueError("Predictions must contain only 0 or 1 values")

        if not np.all(np.isin(target, [0, 1])):
            raise ValueError("Targets must contain only 0 or 1 values")

        # Compute confusion matrix for this split and add to aggregate
        cm = confusion_matrix(target, pred, labels=[0, 1])
        aggregated_cm += cm

    # Normalize the aggregated confusion matrix to get percentages
    total_samples = np.sum(aggregated_cm)
    normalized_cm = aggregated_cm / total_samples * 100

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create a heatmap without default annotations
    sns.heatmap(normalized_cm,
                annot=False,  # We'll add custom annotations
                fmt='.1f',
                cmap='Blues',
                xticklabels=[f'Predicted {labels[0]}', f'Predicted {labels[1]}'],
                yticklabels=[f'True {labels[0]}', f'True {labels[1]}'],
                cbar=False,
                ax=ax)

    # Make the tick labels bold
    for label in ax.get_xticklabels():
        label.set_fontweight('bold')
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')

    # Add custom annotations with both percentage and count
    for i in range(2):
        for j in range(2):
            count = aggregated_cm[i, j]
            percentage = normalized_cm[i, j]
            # Use different colors for better contrast
            text_color = 'white' if percentage > 50 else 'black'
            ax.text(j + 0.5, i + 0.5, f'{percentage:.1f}%\n({count})',
                    ha='center', va='center', fontsize=10,
                    color=text_color)

    plt.title('Confusion Matrix (Aggregated across all splits)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Predicted Label', fontsize=13, fontweight='bold')
    plt.ylabel('True Label', fontsize=13, fontweight='bold')

    # Calculate metrics
    accuracy = (aggregated_cm[0, 0] + aggregated_cm[1, 1]) / total_samples
    precision = aggregated_cm[1, 1] / (aggregated_cm[1, 1] + aggregated_cm[0, 1]) if (aggregated_cm[1, 1] +
                                                                                      aggregated_cm[0, 1]) > 0 else 0
    recall = aggregated_cm[1, 1] / (aggregated_cm[1, 1] + aggregated_cm[1, 0]) if (aggregated_cm[1, 1] + aggregated_cm[
        1, 0]) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Add statistics in a separate text box below the plot
    stats_text = f"Accuracy: {accuracy:.3f}  |  Precision: {precision:.3f}  |  Recall: {recall:.3f}  |  F1-Score: {f1_score:.3f}"
    plt.figtext(0.5, 0.02, stats_text, ha='center', fontsize=11,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)  # Make room for the stats
    plt.show()


# Example usage:
if __name__ == "__main__":
    # Create some example data
    np.random.seed(42)

    # Simulate predictions and targets for 3 splits
    preds = [
        np.random.choice([0, 1], size=100, p=[0.6, 0.4]),
        np.random.choice([0, 1], size=100, p=[0.5, 0.5]),
        np.random.choice([0, 1], size=100, p=[0.7, 0.3])
    ]

    targets = [
        np.random.choice([0, 1], size=100, p=[0.6, 0.4]),
        np.random.choice([0, 1], size=100, p=[0.5, 0.5]),
        np.random.choice([0, 1], size=100, p=[0.7, 0.3])
    ]

    # Plot the confusion matrix
    plot_confusion_matrix(preds, targets, ("Control", "FSmoker"))