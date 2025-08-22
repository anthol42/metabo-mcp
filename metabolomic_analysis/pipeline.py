import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path, PurePath

# Import your existing modules
import pickle
from utils import build_report, save_fig
from data import Dataloader, Imputer
from split import Spliter
from optim import Optimizer, ParamRange
from results import plot_confusion_matrix, feature_logplot, feature_heatmap, plot_performances, make_feat_imp, \
    get_important_features_df
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from pyscm import SetCoveringMachineClassifier
from randomscm import RandomScmClassifier
from typing import Tuple, Dict, List
from xgboost import XGBClassifier


def get_safe_download_directory():
    """Get download directory or fallback to desktop/home"""
    home = Path.home()

    # Try common download folder names
    download_names = ["Downloads", "Téléchargements", "Descargas", "Download"]

    for name in download_names:
        path = home / name
        if path.exists():
            return path

    # Fallback to Desktop if it exists, otherwise home
    desktop = home / "Desktop"
    return desktop if desktop.exists() else home


class MLPipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ML Pipeline Runner")
        self.root.geometry("600x600")

        # Variables to store file paths and parameters
        self.data_path = tk.StringVar()
        self.metadata_path = tk.StringVar()
        self.target_column = tk.StringVar()
        self.id_column = tk.StringVar(value="Id")
        self.output_path = tk.StringVar(value=str(get_safe_download_directory() / "giga_view_report.pdf"))
        self.num_splits = tk.StringVar(value="10")
        self.max_prop_diff = tk.StringVar(value="0.2")

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # Data file selection
        ttk.Label(main_frame, text="Data File:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.data_path, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E),
                                                                          padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_data_file).grid(row=row, column=2, padx=5)
        row += 1

        # Metadata file selection
        ttk.Label(main_frame, text="Metadata File:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.metadata_path, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E),
                                                                              padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_metadata_file).grid(row=row, column=2, padx=5)
        row += 1

        # Target column
        ttk.Label(main_frame, text="Target Column:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.target_column, width=20).grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1

        # ID column
        ttk.Label(main_frame, text="ID Column:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.id_column, width=20).grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1

        # Output file
        ttk.Label(main_frame, text="Output Report:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E),
                                                                            padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output_file).grid(row=row, column=2, padx=5)
        row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E),
                                                            pady=10)
        row += 1

        # Advanced parameters label
        ttk.Label(main_frame, text="Advanced Parameters:", font=('TkDefaultFont', 10, 'bold')).grid(row=row, column=0,
                                                                                                    columnspan=3,
                                                                                                    sticky=tk.W,
                                                                                                    pady=(5, 2))
        row += 1

        # Number of splits
        ttk.Label(main_frame, text="Number of Splits:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.num_splits, width=10).grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1

        # Max proportion difference
        ttk.Label(main_frame, text="Max Inbalance:").grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.max_prop_diff, width=10).grid(row=row, column=1, sticky=tk.W, padx=5)
        row += 1

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E),
                                                            pady=10)
        row += 1

        # Run button
        self.run_button = ttk.Button(main_frame, text="Run Pipeline", command=self.run_pipeline)
        self.run_button.grid(row=row, column=0, columnspan=3, pady=10)
        row += 1

        # Progress bar (changed to determinate mode)
        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=400)
        self.progress.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1

        # Progress percentage label
        self.progress_label = ttk.Label(main_frame, text="0%")
        self.progress_label.grid(row=row, column=0, columnspan=3, pady=2)
        row += 1

        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to run pipeline")
        self.status_label.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1

        # Log text area
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)

        self.log_text = tk.Text(log_frame, height=8, width=70)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def browse_data_file(self):
        filename = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.data_path.set(filename)

    def browse_metadata_file(self):
        filename = filedialog.askopenfilename(
            title="Select Metadata File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.metadata_path.set(filename)

    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save Report As",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)

    def log(self, message):
        """Add message to log text area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_progress(self, current_step, total_steps, phase=""):
        """Update progress bar and label"""
        progress_value = (current_step / total_steps) * 100
        self.progress['value'] = progress_value
        self.progress_label.config(text=f"{progress_value:.1f}%")
        if phase:
            self.status_label.config(text=f"{phase} - {progress_value:.1f}% complete")
        self.root.update_idletasks()

    def validate_inputs(self):
        """Validate all required inputs"""
        if not self.data_path.get():
            messagebox.showerror("Error", "Please select a data file")
            return False
        if not self.metadata_path.get():
            messagebox.showerror("Error", "Please select a metadata file")
            return False
        if not os.path.exists(self.data_path.get()):
            messagebox.showerror("Error", "Data file does not exist")
            return False
        if not os.path.exists(self.metadata_path.get()):
            messagebox.showerror("Error", "Metadata file does not exist")
            return False
        if not self.target_column.get():
            messagebox.showerror("Error", "Please specify target column")
            return False
        if not self.id_column.get():
            messagebox.showerror("Error", "Please specify ID column")
            return False
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify output report path")
            return False

        try:
            int(self.num_splits.get())
            float(self.max_prop_diff.get())
        except ValueError:
            messagebox.showerror("Error", "Number of splits must be integer, max proportion diff must be number")
            return False

        return True

    def run_pipeline_thread(self):
        """Run the ML pipeline in a separate thread"""
        try:
            # Define algorithm grids
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
                }),
                (XGBClassifier, {
                    "learning_rate": ParamRange(0.005, 0.3, log=True),
                    "max_depth": ParamRange(2, 20, integer=True),
                    "n_estimators": ParamRange(10, 500, integer=True),
                    "subsample": ParamRange(0.5, 1.)
                })
            ]

            # Calculate total steps for progress tracking
            num_splits = int(self.num_splits.get())
            num_algorithms = len(algogrids)

            # Progress phases with weights
            phases = {
                "data_loading": 1,  # 1% for data loading and preprocessing
                "model_training": 98,  # 80% for model training (main part)
                "report_generation": 1  # 1% for report generation
            }

            current_progress = 0
            total_progress = 100

            # Phase 1: Data loading and preprocessing
            self.update_progress(current_progress, total_progress, "Loading and preprocessing data")
            self.log("Loading data...")

            dataloader = Dataloader(
                data_path=self.data_path.get(),
                metadata_path=self.metadata_path.get(),
                target_column=self.target_column.get(),
                id_column=self.id_column.get(),
                index_col=None
            )
            X, y, pairs = dataloader.get_data(dataset_index=0)
            self.log(f"Data loaded: {X.shape[0]} samples, {X.shape[1]} features")

            self.update_progress(current_progress, total_progress, "Imputing missing values")

            # Impute based on class median
            self.log("Imputing missing values...")
            imputer = Imputer()
            X, y = imputer.impute(X, y)

            self.update_progress(current_progress, total_progress, "Creating data splits")

            # Split data
            self.log(f"Creating {self.num_splits.get()} splits...")
            splitter = Spliter(
                num_splits=num_splits,
                max_proportion_diff=float(self.max_prop_diff.get())
            )
            splits = splitter.split(X, y)

            current_progress += phases["data_loading"]
            self.update_progress(current_progress, total_progress, "Starting model training")

            inverse = False
            results: List[Dict[str, Tuple[Optimizer, np.ndarray, np.ndarray, float, float]]] = []

            # Phase 2: Model training (main progress tracking)
            total_training_steps = num_splits * num_algorithms
            completed_training_steps = 0

            # Run training on each split
            for i, split in enumerate(splits):
                self.log(f"Processing split {i + 1}/{len(splits)}")
                X_train, X_test, y_train, y_test = split.X_train, split.X_test, split.y_train, split.y_test

                if inverse:
                    y_train = 1 - y_train
                    y_test = 1 - y_test

                results.append({})
                for j, (algo_cls, params) in enumerate(algogrids):
                    self.log(f"  Training {algo_cls.__name__}...")

                    # Update progress for current model training
                    training_progress = current_progress + (completed_training_steps / total_training_steps) * phases[
                        "model_training"]
                    self.update_progress(training_progress, total_progress,
                                         f"Split {i + 1}/{num_splits} - {algo_cls.__name__} ({j + 1}/{num_algorithms})")

                    # Create the optimizer
                    optim = Optimizer(
                        model_cls=algo_cls,
                        n=100,
                        cv=5,
                        param_grid=params
                    )
                    optim.fit(X_train, y_train)
                    train_score = optim.score(X_train, y_train)
                    test_score = optim.score(X_test, y_test)
                    self.log(f"    Test score: {test_score:.4f}")

                    results[i][algo_cls.__name__] = (
                        optim,
                        optim.model.predict(X_test),
                        y_test,
                        train_score,
                        test_score,
                    )

                    completed_training_steps += 1

            # Update progress after training completion
            current_progress += phases["model_training"]
            self.update_progress(current_progress, total_progress, "Training completed, generating report")

            # Phase 3: Report generation
            # Save intermediate results
            self.log("Saving intermediate results...")
            with open('tmp_results.pkl', 'wb') as f:
                pickle.dump(results, f)

            # Generate visualizations
            self.log("Generating performance plots...")
            plot_performances(results)
            perf = save_fig()

            models = results[0].keys()
            preds = {model: [item[model][1] for item in results] for model in models}
            targets = {model: [item[model][2] for item in results] for model in models}

            self.log("Generating confusion matrices...")
            cms = []
            for model in models:
                labels = split.targets[::-1] if inverse else split.targets
                plot_confusion_matrix(preds[model], targets[model], labels=labels, model_name=model)
                cms.append(save_fig())


            # Generate feature importance plots
            self.log("Analyzing feature importance...")
            optimizers = {model: [item[model][0] for item in results] for model in models}
            feature_importances = make_feat_imp(optimizers, split.features)

            feature_heatmap(feature_importances, 5)
            hm = save_fig()
            feature_logplot(feature_importances, 10)
            logplot = save_fig()
            df = get_important_features_df(feature_importances, top_n=10)


            # Build final report
            self.log("Building final report...")
            data_info = f"Number of samples: {len(X)}\n\nNumber of features: {X.shape[1]}\n\n"
            build_report([perf, *cms, hm, logplot], df, output_path=self.output_path.get(), additional_info=data_info)

            all_feat = get_important_features_df(feature_importances, top_n=10_000)
            path = ".".join(self.output_path.get().split(".")[:-1])
            all_feat.to_csv(path + ".csv", index=False)

            # Final progress update
            self.update_progress(100, 100, "Pipeline completed successfully!")

            self.log(f"Pipeline completed! Report saved to: {self.output_path.get()}")
            self.status_label.config(text=f"Pipeline completed successfully!")

            # Show success message
            messagebox.showinfo("Success",
                                f"Pipeline completed successfully!\nReport saved to: {self.output_path.get()}")

        except Exception as e:
            self.log(f"Error occurred: {str(e)}")
            self.status_label.config(text="Error occurred - check log")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            # Re-enable button
            self.run_button.config(state='normal')

    def run_pipeline(self):
        """Main function to run the pipeline"""
        if not self.validate_inputs():
            return

        # Disable button and reset progress bar
        self.run_button.config(state='disabled')
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="Starting pipeline...")
        self.log_text.delete(1.0, tk.END)  # Clear log

        # Run pipeline in separate thread to avoid freezing GUI
        thread = threading.Thread(target=self.run_pipeline_thread)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    app = MLPipelineGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()