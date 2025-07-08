import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Tuple
import numpy as np


def plot_performances(acc: Dict[str, Tuple[pd.Series, pd.Series]]):
    """
    Make a bar plot with uncertainty bars of the performances of the model given a dictionary of accuracies.
    The keys of the dictionary are the names of the models and the values is a series containing the accuracies on
    each split.

    The error bars represent the standard deviation of the accuracies across the splits.
    :param acc: A dictionary where keys are model names and values are a tuple of two pandas Series: train and test
    balanced accuracies.
    :return: The figure
    """
    # Extract model names and compute means and stds for train and test
    model_names = list(acc.keys())
    train_means = [acc[model][0].mean() for model in model_names]
    train_stds = [acc[model][0].std() for model in model_names]
    test_means = [acc[model][1].mean() for model in model_names]
    test_stds = [acc[model][1].std() for model in model_names]

    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Set up positions for grouped bars
    x_pos = np.arange(len(model_names))
    bar_width = 0.4  # Width of each bar

    # Get theme colors (use matplotlib's default color cycle)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    train_color = colors[0]  # First theme color
    test_color = colors[1]  # Second theme color

    # Create the grouped bars
    train_bars = ax.bar(x_pos - bar_width / 2, train_means, bar_width,
                        yerr=train_stds, capsize=5, label='Train',
                        color=train_color)

    test_bars = ax.bar(x_pos + bar_width / 2, test_means, bar_width,
                       yerr=test_stds, capsize=5, label='Test',
                       color=test_color)

    # Customize the plot
    ax.set_xlabel('Model', fontsize=12)
    ax.set_ylabel('Balanced Accuracy', fontsize=12)
    ax.set_title('Model Performance Comparison: Train vs Test', fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(model_names)
    ax.set_ylim(0, 1)

    # Add legend
    ax.legend(fontsize=11)

    # Add grid for better readability
    ax.grid(True, alpha=0.3, axis='y')

    # Rotate x-axis labels if there are many models
    if len(model_names) > 5:
        plt.xticks(rotation=45, ha='right')

    # Add value labels on top of bars
    for bar, mean, std in zip(train_bars, train_means, train_stds):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + std / 2,
                f'{mean:.3f}', ha='center', va='bottom', fontsize=9)

    for bar, mean, std in zip(test_bars, test_means, test_stds):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + std / 2,
                f'{mean:.3f}', ha='center', va='bottom', fontsize=9)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    return fig


if __name__ == "__main__":
    import numpy as np

    # Create sample data with train and test accuracies for different models
    np.random.seed(42)  # For reproducible results

    # Simulate train and test accuracy data for different models across multiple splits
    test_data = {
        'ResNet-18': (
            pd.Series([0.92, 0.94, 0.91, 0.93, 0.92, 0.95, 0.91, 0.94, 0.92, 0.93]),  # Train
            pd.Series([0.85, 0.87, 0.84, 0.86, 0.85, 0.88, 0.84, 0.87, 0.85, 0.86])  # Test
        ),
        'ResNet-50': (
            pd.Series([0.96, 0.98, 0.95, 0.97, 0.96, 0.99, 0.95, 0.98, 0.96, 0.97]),  # Train
            pd.Series([0.89, 0.91, 0.88, 0.90, 0.89, 0.92, 0.88, 0.91, 0.89, 0.90])  # Test
        ),
        'VGG-16': (
            pd.Series([0.89, 0.91, 0.88, 0.90, 0.89, 0.92, 0.88, 0.91, 0.89, 0.90]),  # Train
            pd.Series([0.82, 0.84, 0.81, 0.83, 0.82, 0.85, 0.81, 0.84, 0.82, 0.83])  # Test
        ),
        'DenseNet-121': (
            pd.Series([0.94, 0.96, 0.93, 0.95, 0.94, 0.97, 0.93, 0.96, 0.94, 0.95]),  # Train
            pd.Series([0.87, 0.89, 0.86, 0.88, 0.87, 0.90, 0.86, 0.89, 0.87, 0.88])  # Test
        ),
        'EfficientNet-B0': (
            pd.Series([0.97, 0.99, 0.96, 0.98, 0.97, 1.00, 0.96, 0.99, 0.97, 0.98]),  # Train
            pd.Series([0.90, 0.92, 0.89, 0.91, 0.90, 0.93, 0.89, 0.92, 0.90, 0.91])  # Test
        )
    }

    # Test the function
    fig = plot_performances(test_data)

    # Display the plot
    plt.show()

    # Print some statistics for verification
    print("Model Performance Summary:")
    print("-" * 60)
    print(f"{'Model':<15} | {'Train Mean':<10} | {'Train Std':<9} | {'Test Mean':<10} | {'Test Std':<9}")
    print("-" * 60)
    for model, (train_acc, test_acc) in test_data.items():
        train_mean, train_std = train_acc.mean(), train_acc.std()
        test_mean, test_std = test_acc.mean(), test_acc.std()
        print(f"{model:<15} | {train_mean:<10.3f} | {train_std:<9.3f} | {test_mean:<10.3f} | {test_std:<9.3f}")