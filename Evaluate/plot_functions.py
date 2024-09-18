"""
Module: VSLAM-LAB - Compare - plot_functions.py
- Author: Alejandro Fontan Villacampa
- Version: 1.0
- Created: 2024-07-04
- Updated: 2024-07-04
- License: GPLv3 License
- List of Known Dependencies;
    * ...

This module provides functions for generating various types of plots to visualize experiment data across multiple datasets and sequences.

Functions included:
- boxplot_exp_seq: Generates box plots for different experiments and sequences within multiple datasets.
- radar_seq: Creates a radar plot showing the relative performance across different sequences and datasets based on a specified metric.
- plot_cum_error: Generates and saves cumulative error plots for different datasets, sequences, and experiments.
- create_and_show_canvas: Creates a canvas of resized images and displays it.
"""

import glob
import math
import os
import random
from bisect import bisect_left
from math import pi

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.patches import Patch
from sklearn.decomposition import PCA

from utilities import VSLAM_LAB_EVALUATION_FOLDER
from utilities import list_image_files_in_folder

random.seed(6)
colors_all = mcolors.CSS4_COLORS
colors = list(colors_all.keys())
random.shuffle(colors)

import logging

logging.getLogger('matplotlib').setLevel(logging.ERROR)


def copy_axes_properties(source_ax, target_ax):
    for line in source_ax.get_lines():
        target_ax.plot(line.get_xdata(), line.get_ydata(), color=line.get_color(), linestyle=line.get_linestyle())

    for patch in source_ax.patches:
        new_patch = patch.__class__(xy=patch.get_xy(), width=patch.get_width(), height=patch.get_height(),
                                    color=patch.get_facecolor())
        target_ax.add_patch(new_patch)

    target_ax.set_xlim(source_ax.get_xlim())
    target_ax.set_ylim(source_ax.get_ylim())

    target_ax.set_xticks(source_ax.get_xticks())
    target_ax.set_xticklabels(source_ax.get_xticklabels())


def plot_trajectories(dataset_sequences, exp_names, dataset_nicknames, experiments, accuracies, comparison_path):
    # Figure dimensions
    num_datasets = len(dataset_sequences)
    num_rows = math.ceil(num_datasets / 5)
    xSize = 12
    ySize = num_rows * 2

    fig, axs = plt.subplots(num_rows, 5, figsize=(xSize, ySize))
    axs = axs.flatten()

    # Create legend handles
    legend_handles = []
    legend_handles.append(Patch(color='black', label='gt'))
    for i_exp, exp_name in enumerate(exp_names):
        legend_handles.append(Patch(color=colors[i_exp], label=exp_names[i_exp]), )

    for i_dataset, (dataset_name, sequence_names) in enumerate(dataset_sequences.items()):
        for i_sequence, sequence_name in enumerate(sequence_names):

            for i_exp, exp_name in enumerate(exp_names):
                vslam_lab_evaluation_folder_seq = os.path.join(experiments[exp_name].folder, dataset_name.upper(),
                                                               sequence_name, VSLAM_LAB_EVALUATION_FOLDER)

                if i_exp == 0:
                    gt_file = os.path.join(vslam_lab_evaluation_folder_seq, 'gt.tum')
                    gt_traj = pd.read_csv(gt_file)
                    pca_df = pd.DataFrame(gt_traj, columns=['tx gt', 'ty gt', 'tz gt'])
                    pca = PCA(n_components=2)
                    pca.fit(pca_df)
                    gt_transformed = pca.transform(pca_df)
                    axs[i_dataset].plot(gt_transformed[:, 0], gt_transformed[:, 1], label='gt', linestyle='-',
                                        color='black')

                search_pattern = os.path.join(vslam_lab_evaluation_folder_seq, '*_KeyFrameTrajectory.tum*')
                files = glob.glob(search_pattern)
                idx = accuracies[dataset_name][sequence_name][exp_name]['rmse'].idxmin()
                aligned_traj = pd.read_csv(files[idx])
                pca_df = pd.DataFrame(aligned_traj, columns=['tx', 'ty', 'tz'])
                pca_df.rename(columns={'tx': 'tx gt', 'ty': 'ty gt', 'tz': 'tz gt'}, inplace=True)
                traj_transformed = pca.transform(pca_df)

                axs[i_dataset].plot(traj_transformed[:, 0], traj_transformed[:, 1],
                                    label=exp_name, marker='.', linestyle='-', color=colors[i_exp])

            axs[i_dataset].grid(True)
            axs[i_dataset].set_title(dataset_nicknames[dataset_name][i_sequence])

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.3)
    plot_name = os.path.join(comparison_path, f"trajectories.eps")
    plt.savefig(plot_name, format='eps')
    plt.show(block=False)


def boxplot_exp_seq(values, dataset_sequences, exp_names, dataset_nicknames, metric_name, comparison_path):
    """
    ------------ Description:
    This function generates a series of box plots for different experiments and sequences within multiple datasets.
    Each dataset's sequences are plotted in a row, with columns representing different metrics or views.

    ------------ Parameters:
    values : dict
        values[dataset_name][sequence_name][exp_name] = pandas.DataFrame()
    dataset_sequences : dict
        dataset_sequences[dataset_name] = list{sequence_names}
    exp_names : list
        exp_names = list{exp_names}
    dataset_nicknames : dict
        dataset_nicknames[dataset_name] = list{sequence_nicknames}
    metric_name : string
        metric_name = "accuracy"
    """

    num_experiments = len(exp_names)
    num_datasets = len(dataset_sequences)

    # Figure dimensions
    width_per_series = 0.05
    num_rows = num_datasets
    num_cols = 4
    xSize = 12
    ySize = num_rows * 2

    fig, axs = plt.subplots(num_rows, num_cols, figsize=(xSize, ySize))
    axs = axs.flatten()

    # Create legend handles
    legend_handles = []
    for i_exp, exp_name in enumerate(exp_names):
        legend_handles.append(Patch(color=colors[i_exp], label=exp_names[i_exp]), )

    # Plot
    for i_dataset, (dataset_name, sequence_names) in enumerate(dataset_sequences.items()):
        y_max_limit_dataset = 0
        y_min_limit_dataset = -1
        for i_exp, exp_name in enumerate(exp_names):
            boxprops = dict(color=colors[i_exp])
            medianprops = dict(color=colors[i_exp])
            whiskerprops = dict(color=colors[i_exp])
            capprops = dict(color=colors[i_exp])
            flierprops = dict(marker='o', color=colors[i_exp], alpha=1.0)

            for sequence_name in sequence_names:
                positions = [(i + 1) * (width_per_series * 1.2) + i_exp * (width_per_series * 1.2) * len(sequence_names)
                             for i in range(len(sequence_names))]

                boxplot_accuracy = axs[num_cols * i_dataset].boxplot(
                    values[dataset_name][sequence_name][exp_name]['rmse'],
                    positions=positions, widths=width_per_series,
                    patch_artist=False,
                    boxprops=boxprops, medianprops=medianprops,
                    whiskerprops=whiskerprops,
                    capprops=capprops, flierprops=flierprops)

                medians = [item.get_ydata()[0] for item in boxplot_accuracy['medians']]
                whiskers = np.concatenate([whisker.get_ydata() for whisker in boxplot_accuracy['whiskers']])
                flier_counts = []
                for flier in boxplot_accuracy['fliers']:
                    flier_counts.append(len(flier.get_ydata()))

                boxplot_accuracy_zoom = axs[num_cols * i_dataset].boxplot(
                    values[dataset_name][sequence_name][exp_name]['rmse'],
                    positions=positions, widths=width_per_series,
                    patch_artist=False,
                    boxprops=boxprops, medianprops=medianprops,
                    whiskerprops=whiskerprops,
                    capprops=capprops, flierprops=flierprops)

                boxplot_num_eval_pts = axs[num_cols * i_dataset + 2].boxplot(
                    values[dataset_name][sequence_name][exp_name]['Number of Evaluation Points'],
                    positions=positions, widths=width_per_series,
                    patch_artist=False,
                    boxprops=boxprops, medianprops=medianprops,
                    whiskerprops=whiskerprops,
                    capprops=capprops, flierprops=flierprops)

                bar_diagram_out_of_dist = axs[num_cols * i_dataset + 1].bar(positions, flier_counts, width_per_series,
                                                                            color=colors[i_exp])
                bar_diagram_num_runs = axs[num_cols * i_dataset + 3].bar(positions,
                                                                         len(values[dataset_name][sequence_name][
                                                                                 exp_name]['rmse']),
                                                                         width_per_series, color=colors[i_exp])

                max_whisker_ = np.max(whiskers)
                median_ = np.median(medians)
                min_whisker_ = np.min(whiskers)

                y_max_limit_dataset_ = (2.0 * max_whisker_ - median_)
                if y_max_limit_dataset_ > y_max_limit_dataset:
                    y_max_limit_dataset = y_max_limit_dataset_

                y_min_limit_dataset_ = (2.0 * min_whisker_ - median_)
                if (y_min_limit_dataset_ < y_min_limit_dataset) or (y_min_limit_dataset < 0):
                    y_min_limit_dataset = y_min_limit_dataset_

        label_positions = [
            (i + 1) * (width_per_series * 1.2) + ((num_experiments - 1) / 2.0) * (width_per_series * 1.2) * len(
                sequence_names)
            for i in range(len(sequence_names))]
        for i in range(0, num_cols):
            axs[num_cols * i_dataset + i].grid(True, linestyle='--', linewidth=0.5, color='gray')
            axs[num_cols * i_dataset + i].set_xticks(label_positions, dataset_nicknames[dataset_name], rotation=0)

        axs[num_cols * i_dataset].set_ylim(y_min_limit_dataset, y_max_limit_dataset)

        if i_dataset == 0:
            axs[0].set_title('Accuracy')
            axs[1].set_title('Out-of-distribution')
            axs[2].set_title('# Evaluation Points')
            axs[3].set_title('# Runs')

    i = 0
    for dataset_name, sequence_names in dataset_sequences.items():
        y_pos = 0.89 - (i * ((0.95 - 0.1) / num_datasets))
        fig.text(0.015, y_pos, dataset_name, va='center', ha='center', rotation='vertical', fontsize=12)
        i = i + 1

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.tight_layout()
    plt.subplots_adjust(left=0.075, top=0.95, bottom=0.1)

    plot_name = os.path.join(comparison_path, f"{metric_name}_boxplot_detailed.eps")
    plt.savefig(plot_name, format='eps')
    plt.show(block=False)

    # Figure dimensions
    num_rows = math.ceil(num_datasets / 5)
    xSize = 12
    ySize = num_rows * 2

    fig, axs_global = plt.subplots(num_rows, 5, figsize=(xSize, ySize))
    axs_global = axs_global.flatten()
    i_dataset = 0
    for dataset_name, sequence_names in dataset_sequences.items():
        copy_axes_properties(axs[i_dataset * num_cols], axs_global[i_dataset])
        axs_global[i_dataset].grid(True, linestyle='--', linewidth=0.5, color='gray')
        axs_global[i_dataset].set_title(dataset_name)
        i_dataset = i_dataset + 1

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    plot_name = os.path.join(comparison_path, f"{metric_name}_boxplot_global.eps")
    plt.savefig(plot_name, format='eps')
    plt.show(block=False)


def radar_seq(values, dataset_sequences, exp_names, dataset_nicknames, metric_name, comparison_path):
    """
     ------------ Description:
    This function creates a radar plot showing the relative performance across different sequences and datasets.
    The performance metric (e.g., accuracy) is normalized by the global median value for each sequence.

    ------------ Parameters:
    values : dict
        values[dataset_name][sequence_name][exp_name] = pandas.DataFrame()
    dataset_sequences : dict
        dataset_sequences[dataset_name] = list{sequence_names}
    exp_names : list
        exp_names = list{exp_names}
    dataset_nicknames : dict
        dataset_nicknames[dataset_name] = list{sequence_nicknames}
    metric_name : string
        metric_name = "accuracy"
    """

    # Create legend handles
    legend_handles = []
    for i_exp, exp_name in enumerate(exp_names):
        legend_handles.append(Patch(color=colors[i_exp], label=exp_names[i_exp]), )

    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))
    all_sequence_names = []
    medians = {}
    median_sequence = {}
    for dataset_name, sequence_names in dataset_sequences.items():
        medians[dataset_name] = {}
        all_sequence_names.extend(dataset_nicknames[dataset_name])
        values_sequence = {}
        for sequence_name in sequence_names:
            medians[dataset_name][sequence_name] = {}
            values_sequence[sequence_name] = pd.Series([])

            for exp_name in exp_names:
                medians[dataset_name][sequence_name][exp_name] = np.median(
                    values[dataset_name][sequence_name][exp_name]['rmse'])
                if values_sequence[sequence_name].empty:
                    values_sequence[sequence_name] = values[dataset_name][sequence_name][exp_name][
                        'rmse']
                else:
                    values_sequence[sequence_name] = pd.concat([values_sequence[sequence_name],
                                                                values[dataset_name][sequence_name][exp_name][
                                                                    'rmse']],
                                                               ignore_index=True)

            median_sequence[sequence_name] = np.median(values_sequence[sequence_name])

    num_vars = len(all_sequence_names)
    iExp = 0
    y = {}
    for experiment_name in exp_names:
        y[experiment_name] = []
        for dataset_name, sequence_names in dataset_sequences.items():
            for sequence_name in sequence_names:
                y[experiment_name].append(
                    medians[dataset_name][sequence_name][experiment_name] / median_sequence[sequence_name])

        #for i,yi in enumerate(y[experiment_name]): #INVERT ACCURACY
        #y[experiment_name][i] = 1/yi

        values_ = y[experiment_name]
        angles = np.linspace(0, 2 * pi, num_vars, endpoint=False).tolist()

        values_ += values_[:1]
        angles += angles[:1]
        ax.plot(angles, values_, color=colors[iExp], marker='o')
        plt.xticks(angles[:-1], all_sequence_names)
        iExp = iExp + 1

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.tight_layout()
    plt.subplots_adjust(top=0.95, bottom=0.15)  # Adjust the top and bottom to make space for the legend

    plot_name = os.path.join(comparison_path, f"{metric_name}_radar.eps")
    plt.savefig(plot_name, format='eps')
    plt.show(block=False)


def plot_cum_error(values, dataset_sequences, exp_names, dataset_nicknames, metric_name, comparison_path):
    """
     ------------ Description:
    This function generates and saves cumulative error plots for different datasets, sequences, and experiments.
    It creates subplots for each sequence within a dataset and plots the cumulative error for each experiment.
    The cumulative error is calculated as the number of values smaller than or equal to each data point.

    ------------ Parameters:
    values : dict
        values[dataset_name][sequence_name][exp_name] = pandas.DataFrame()
    dataset_sequences : dict
        dataset_sequences[dataset_name] = list{sequence_names}
    exp_names : list
        exp_names = list{exp_names}
    dataset_nicknames : dict
        dataset_nicknames[dataset_name] = list{sequence_nicknames}
    metric_name : string
        metric_name = "accuracy"
    """
    num_sequences = 0
    for dataset_name, sequence_names in dataset_sequences.items():
        num_sequences += len(sequence_names)

    num_cols = 5
    num_rows = math.ceil(num_sequences / num_cols)
    x_size = 12
    y_size = num_rows * 2

    fig, axs = plt.subplots(num_rows, num_cols, figsize=(x_size, y_size))
    axs = axs.flatten()

    # Create legend handles
    legend_handles = []
    for i_exp, exp_name in enumerate(exp_names):
        legend_handles.append(Patch(color=colors[i_exp], label=exp_names[i_exp]), )

    j_seq = 0
    for dataset_name, sequence_names in dataset_sequences.items():
        for i_seq, sequence_name in enumerate(sequence_names):
            for i_exp, experiment_name in enumerate(exp_names):
                data = values[dataset_name][sequence_name][experiment_name]['rmse'].tolist()
                sorted_data = sorted(data)
                cumulated_vector = []
                for data_i in sorted_data:
                    count_smaller = bisect_left(sorted_data, data_i)
                    cumulated_vector.append(count_smaller)
                axs[j_seq].plot(sorted_data, cumulated_vector, marker='o', linestyle='-', color=colors[i_exp])

            axs[j_seq].set_title(dataset_nicknames[dataset_name][i_seq])
            axs[j_seq].grid(True, linestyle='--', linewidth=0.5, color='gray')
            j_seq = j_seq + 1

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.25)  # Adjust the top and bottom to make space for the legend

    plot_name = os.path.join(comparison_path, f"{metric_name}_cummulated_error.eps")
    plt.savefig(plot_name, format='eps')
    plt.show(block=False)


def create_and_show_canvas(dataset_sequences, VSLAMLAB_BENCHMARK, comparison_path):
    image_paths = []

    for dataset_name, sequence_names in dataset_sequences.items():
        for sequence_name in sequence_names:
            image_files = list_image_files_in_folder(
                os.path.join(VSLAMLAB_BENCHMARK, dataset_name.upper(), sequence_name, 'rgb'))
            image_paths.append(
                os.path.join(VSLAMLAB_BENCHMARK, dataset_name.upper(), sequence_name, 'rgb', image_files[0]))

    m = 5
    n = math.ceil(len(image_paths) / m)

    canvas_width = m * 640
    canvas_height = n * 480

    # Load the images
    images = [Image.open(path) for path in image_paths]

    # Calculate target size for each image to fit the canvas
    img_width = canvas_width // m
    img_height = canvas_height // n
    target_size = (img_width, img_height)

    # Resize all images to the target size
    resized_images = []
    for img in images:
        resized_images.append(img.resize(target_size, Image.LANCZOS))
    images = resized_images

    # Create a blank canvas with a white background
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')

    # Paste each image into the correct position
    for i in range(n):
        for j in range(m):
            index = i * m + j
            if index < len(images):
                img = images[index]
                x_offset = j * img_width
                y_offset = i * img_height
                canvas.paste(img, (x_offset, y_offset))

    # Save the canvas
    plot_name = os.path.join(comparison_path, 'canvas_sequences.png')
    canvas.save(plot_name)

    # Show the canvas
    plt.figure(figsize=(12.8, 6.4))  # Convert pixels to inches for display
    plt.imshow(canvas)
    plt.axis('off')  # Hide the axis
    plt.show(block=False)
