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
from bisect import bisect_left, bisect_right
from math import pi

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.patches import Patch
from sklearn.decomposition import PCA

from path_constants import VSLAM_LAB_EVALUATION_FOLDER, VSLAMLAB_BENCHMARK
from utilities import list_image_files_in_folder
from Baselines.baseline_utilities import get_baseline
from Datasets.get_dataset import get_dataset

import matplotlib.ticker as ticker
from matplotlib.transforms import ScaledTranslation

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


def plot_trajectories(dataset_sequences, exp_names, 
                      dataset_nicknames, experiments,
                        accuracies, comparison_path):
    num_trajectories = 0
    for i_dataset, (dataset_name, sequence_names) in enumerate(dataset_sequences.items()):
        for i_sequence, sequence_name in enumerate(sequence_names):
            num_trajectories = num_trajectories + 1

    # Figure dimensions
    num_rows = math.ceil(num_trajectories / 5)
    xSize = 12
    ySize = num_rows * 2

    fig, axs = plt.subplots(num_rows, 5, figsize=(xSize, ySize))
    axs = axs.flatten()

    # Create legend handles
    legend_handles = []
    legend_handles.append(Patch(color='black', label='gt'))
    for i_exp, exp_name in enumerate(exp_names):
        legend_handles.append(Patch(color=colors[i_exp], label=exp_names[i_exp]), )

    i_traj = 0
    there_is_gt = False
    for i_dataset, (dataset_name, sequence_names) in enumerate(dataset_sequences.items()):
        for i_sequence, sequence_name in enumerate(sequence_names):
            #x_max , y_max = 0, 0
            aligment_with_gt = False
            for i_exp, exp_name in enumerate(exp_names):
                vslam_lab_evaluation_folder_seq = os.path.join(experiments[exp_name].folder, dataset_name.upper(),
                                                               sequence_name, VSLAM_LAB_EVALUATION_FOLDER)

                if accuracies[dataset_name][sequence_name][exp_name].empty:
                    continue

                if not aligment_with_gt:                   
                    accu = accuracies[dataset_name][sequence_name][exp_name]['rmse'] / accuracies[dataset_name][sequence_name][exp_name]['num_tracked_frames']
                    idx = accu.idxmin()
                    gt_file = os.path.join(vslam_lab_evaluation_folder_seq, f'{idx:05d}_gt.tum')
                    there_is_gt = False
                    if os.path.exists(gt_file):
                        there_is_gt = True
                        gt_traj = pd.read_csv(gt_file, delimiter=' ')
                        pca_df = pd.DataFrame(gt_traj, columns=['tx', 'ty', 'tz'])
                        pca = PCA(n_components=2)
                        pca.fit(pca_df)
                        gt_transformed = pca.transform(pca_df)
                        x_shift = 1.2*gt_transformed[:, 0].min()
                        y_shift = 1.2* gt_transformed[:, 1].min()
                        x_max = 1.2* gt_transformed[:, 0].max() - x_shift
                        y_max = 1.2* gt_transformed[:, 1].max() - y_shift
                        axs[i_traj].plot(gt_transformed[:, 0]-x_shift, gt_transformed[:, 1]-y_shift, label='gt', linestyle='-', color='black')
                    else:
                        x_shift = 0
                        y_shift = 0
                        x_max = 1
                        y_max = 1
                    aligment_with_gt = True

                search_pattern = os.path.join(vslam_lab_evaluation_folder_seq, '*_KeyFrameTrajectory.tum*')
                files = glob.glob(search_pattern)
        
                aligned_traj = pd.read_csv(files[idx], delimiter=' ')
                pca_df = pd.DataFrame(aligned_traj, columns=['tx', 'ty', 'tz'])
                if len(files) == 0:
                    continue
                if there_is_gt:
                    traj_transformed = pca.transform(pca_df)
                else:
                    traj_transformed = pca_df
                    traj_transformed = traj_transformed.to_numpy()

                baseline = get_baseline(experiments[exp_name].module)
                axs[i_traj].plot(traj_transformed[:, 0]-x_shift, traj_transformed[:, 1]-y_shift,
                                    label=exp_name, marker='.', linestyle='-', color=baseline.color)

            x_ticks = [round(x_max, 1)]
            y_ticks = [0,round(y_max, 1)]
            axs[i_traj].set_xticks(x_ticks)
            axs[i_traj].set_yticks(y_ticks)

            # Format tick labels to 1 decimal place
            axs[i_traj].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}'))
            axs[i_traj].yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}'))

            # Add minor ticks for the grid (every 10% of the axis range)
            axs[i_traj].xaxis.set_minor_locator(ticker.MultipleLocator(x_max / 4))
            axs[i_traj].yaxis.set_minor_locator(ticker.MultipleLocator(y_max / 4))

            # Enable the grid for both major and minor ticks, but keep labels only for major ticks
            axs[i_traj].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
            axs[i_traj].spines['top'].set_visible(False)   # Remove top border
            axs[i_traj].spines['right'].set_visible(False) # Remove right border
            #axs[i_traj].spines['left'].set_visible(False)  # Remove left border (optional)
            #axs[i_traj].spines['bottom'].set_visible(False) # Remove bottom border (optional)

            # Hide minor tick labels while keeping the minor grid lines
            axs[i_traj].tick_params(axis='both', which='minor', labelbottom=False, labelleft=False)
            axs[i_traj].tick_params(axis='y', labelsize=20, rotation=90) 
            axs[i_traj].tick_params(axis='x', labelsize=20, rotation=0) 

            axs[i_traj].tick_params(axis='x', pad=10) 
            axs[i_traj].set_xticklabels([f"{x_ticks[0]:.2f}"], ha='right')  
            axs[i_traj].set_yticklabels([f"{y_ticks[0]:.0f}",f"{y_ticks[1]:.2f}"])  
            
            i_traj = i_traj + 1


    plt.tight_layout()
    plot_name = os.path.join(comparison_path, f"trajectories.pdf")
    plt.savefig(plot_name, format='pdf')

    i_traj = 0
    for i_dataset, (dataset_name, sequence_names) in enumerate(dataset_sequences.items()):
        for i_sequence, sequence_name in enumerate(sequence_names):
            for i_exp, exp_name in enumerate(exp_names):
                axs[i_traj].set_title(dataset_nicknames[dataset_name][i_sequence])
            i_traj = i_traj + 1    
    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.subplots_adjust(bottom=0.3)
    plt.show(block=False)



def boxplot_exp_seq(values, dataset_sequences, metric_name, comparison_path, experiments, shared_scale = False):

    def set_format(tick):
        if tick == 0:
            return f"0"
        return f"{tick:.1e}"

    # Get number of sequences
    num_sequences = 0
    splts = {}
    for dataset_name, sequence_names in dataset_sequences.items():
        dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
        for sequence_name in sequence_names:
            splts[sequence_name]= {}
            splts[sequence_name]['id']= num_sequences
            splts[sequence_name]['dataset_name']= dataset_name
            splts[sequence_name]['nickname']= dataset.get_sequence_nickname(sequence_name)
            splts[sequence_name]['success']= True
            num_sequences += 1

    exp_names = list(experiments.keys())

    # Figure dimensions
    NUM_COLS = 5
    NUM_ROWS = math.ceil(num_sequences / NUM_COLS)
    XSIZE, YSIZE = 12, 2 * NUM_ROWS + 0.5
    WIDTH_PER_SERIES = min(XSIZE / len(exp_names), 0.4)
    FONT_SIZE = 15
    fig, axs = plt.subplots(NUM_ROWS, NUM_COLS, figsize=(XSIZE, YSIZE))
    axs = axs.flatten()

    # Create legend handles
    legend_handles = []
    colors = {}
    for i_exp, exp_name in enumerate(exp_names):
        baseline = get_baseline(experiments[exp_name].module)   
        colors[exp_name] = baseline.color
        legend_handles.append(Patch(color=colors[exp_name], label=exp_names[i_exp]))
        
    # Plot boxplots
    whisker_min = {}
    whisker_max = {}
    for sequence_name, splt in splts.items():
        whisker_min_seq, whisker_max_seq = float('inf'), float('-inf')
        for i_exp, exp_name in enumerate(exp_names):

            values_seq_exp = values[splt['dataset_name']][sequence_name][exp_name]
            if values_seq_exp.empty:
                continue
            boxprops = medianprops = whiskerprops = capprops = dict(color=colors[exp_name])
            flierprops = dict(marker='o', color=colors[exp_name], alpha=1.0)
            positions = [i_exp * WIDTH_PER_SERIES]   
            boxplot_accuracy = axs[splt['id']].boxplot(
                values_seq_exp[metric_name],
                positions=positions, widths=WIDTH_PER_SERIES,
                patch_artist=False,
                boxprops=boxprops, medianprops=medianprops,
                whiskerprops=whiskerprops,
                capprops=capprops, flierprops=flierprops)
            whisker_values = [line.get_ydata()[1] for line in boxplot_accuracy['whiskers']]
            whisker_min_seq = min(whisker_min_seq, min(whisker_values))
            whisker_max_seq = max(whisker_max_seq, max(whisker_values))

        width = max(0.1 * (whisker_max_seq - whisker_min_seq), 1e-6)
        if np.isinf(whisker_max_seq) or np.isinf(whisker_min_seq):
            splts[sequence_name]['success']= False
            whisker_max[sequence_name] = np.nan
            whisker_min[sequence_name] = np.nan
        else:
            whisker_max[sequence_name] = whisker_max_seq + width
            whisker_min[sequence_name] = whisker_min_seq - width

    # Adjust plot properties for paper
    max_value, min_value = max(whisker_max.values()), min(whisker_min.values())

    if shared_scale:
        whisker_max = {key: max_value for key in whisker_max}
        whisker_min = {key: 0 for key in whisker_min}

    for sequence_name, splt in splts.items():
        if splt['success'] == False:
            axs[splt['id']].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
            axs[splt['id']].set_xticklabels([])
            axs[splt['id']].set_yticklabels([])
            continue

        whisker_max_seq = whisker_max[sequence_name]
        whisker_min_seq = whisker_min[sequence_name]
       
        yticks = [whisker_min_seq, whisker_max_seq]

        axs[splt['id']].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        axs[splt['id']].set_xticklabels([])
        axs[splt['id']].set_ylim(yticks)
        axs[splt['id']].tick_params(axis='y', labelsize=FONT_SIZE) 
        axs[splt['id']].yaxis.set_minor_locator(ticker.MultipleLocator((whisker_max_seq - whisker_min_seq) / 4))
        if not shared_scale:    
            axs[splt['id']].set_yticks(yticks)
            tick_labels = axs[splt['id']].get_yticklabels()
            if whisker_max_seq == max_value:
                tick_labels[1].set_color("#CD3232")  
            if whisker_min_seq == min_value:
                tick_labels[0].set_color("#32CD32")      
            tick_labels[0].set_transform(tick_labels[0].get_transform() + ScaledTranslation(0.9, -0.15, fig.dpi_scale_trans))
            tick_labels[1].set_transform(tick_labels[1].get_transform() + ScaledTranslation(0.9, +0.15, fig.dpi_scale_trans))
            axs[splt['id']].set_yticklabels([set_format(tick) for tick in yticks])

        else:
            if splt['id'] == 0:
                axs[splt['id']].set_yticks(yticks)
                axs[splt['id']].tick_params(axis="y", rotation=90)
                axs[splt['id']].set_yticklabels([set_format(tick) for tick in yticks])
            else:
                axs[splt['id']].set_yticks([])   

        
    plt.tight_layout()
    plot_name = os.path.join(comparison_path, f"{metric_name}_boxplot_paper.pdf")
    if shared_scale:
        plot_name = plot_name.replace(".pdf", "_shared_scale.pdf")
    plt.savefig(plot_name, format='pdf')

    # Adjust plot properties for display
    for sequence_name, splt in splts.items():
        if shared_scale:
            axs[splt['id']].set_title(splt['nickname'], fontsize=FONT_SIZE,  fontweight='bold')
        else:
            axs[splt['id']].set_title(splt['nickname'], fontsize=FONT_SIZE, fontweight='bold', pad=30)

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles), fontsize=FONT_SIZE)

    if shared_scale:
        plt.tight_layout(rect=[0, 0.15, 1, 0.95])
    else:
        fig.set_size_inches(XSIZE, 2*YSIZE)
        plt.tight_layout(rect=[0, 0.10, 1, 0.95])

    plot_name = os.path.join(comparison_path, f"{metric_name}_boxplot.pdf")
    if shared_scale:
        plot_name = plot_name.replace(".pdf", "_shared_scale.pdf")
    plt.savefig(plot_name, format='pdf')
    if shared_scale:
        fig.canvas.manager.set_window_title("Accuracy (shared scale)")
    else:
        fig.canvas.manager.set_window_title("Accuracy")
    plt.show(block=False)

def radar_seq(values, dataset_sequences, exp_names, dataset_nicknames, metric_name, comparison_path, experiments):
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
        baseline = get_baseline(experiments[exp_name].module)
        legend_handles.append(Patch(color=baseline.color, label=exp_names[i_exp]), )

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
                values_dataset_sequence_exp = values[dataset_name][sequence_name][exp_name].copy()
                if values_dataset_sequence_exp.empty:
                    values_dataset_sequence_exp['rmse'] = pd.notna

                medians[dataset_name][sequence_name][exp_name] = np.median(values_dataset_sequence_exp['rmse'])    
                
                if values_sequence[sequence_name].empty:
                    values_sequence[sequence_name] = values_dataset_sequence_exp['rmse']
                else:
                    values_sequence[sequence_name] = pd.concat([values_sequence[sequence_name],
                                                                values_dataset_sequence_exp['rmse']],
                                                               ignore_index=True)

            median_sequence[sequence_name] = np.min(values_sequence[sequence_name])

    num_vars = len(all_sequence_names)
    iExp = 0
    y = {}
    for experiment_name in exp_names:
        baseline = get_baseline(experiments[experiment_name].module)
        y[experiment_name] = []
        for dataset_name, sequence_names in dataset_sequences.items():
            for sequence_name in sequence_names:
                y[experiment_name].append(
                    medians[dataset_name][sequence_name][experiment_name] / median_sequence[sequence_name])

        #for i,yi in enumerate(y[experiment_name]): #INVERT ACCURACY
        #y[experiment_name][i] = 1/yi

        values_ = np.clip(y[experiment_name], 0, 3).tolist() 
        angles = np.linspace(0, 2 * pi, num_vars, endpoint=False).tolist()

        values_ += values_[:1]
        angles += angles[:1]

        ax.plot(angles, values_, color=baseline.color, marker='o', linewidth=6)
        ax.plot(np.linspace(0, 2 * np.pi, 100), [2.75] * 100, linestyle="dashed", color="red", linewidth=1)
        #ax.plot(np.linspace(0, 2 * np.pi, 100), [2.72] * 100, linestyle="dashed", color="green", linewidth=2)
        ax.set_ylim(0, 3)
        plt.xticks(angles[:-1], all_sequence_names)
        #ax.set_xticklabels(all_sequence_names, fontsize=26)


        #current_yticks = ax.get_yticks()
        #new_yticks = current_yticks[:-1]  # Exclude the last tick
        #ax.set_yticks(new_yticks)
        #ax.set_yticklabels([str(tick) for tick in new_yticks], fontsize=12)
        ax.set_yticklabels(['', 1, '', '',  '', 3], fontsize=24)   
        ax.tick_params(labelsize=30) 
        ax.set_xticklabels(all_sequence_names, fontsize=30, fontweight="bold")
        iExp = iExp + 1

    
    plt.tight_layout()
    plot_name = os.path.join(comparison_path, f"{metric_name}_radar.pdf")
    plt.savefig(plot_name, format='pdf')
    plt.subplots_adjust(top=0.95, bottom=0.15)  # Adjust the top and bottom to make space for the legend
    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.show(block=False)


def plot_cum_error(values, dataset_sequences, exp_names, dataset_nicknames, metric_name, comparison_path, experiments):
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
            min_x = float('inf')
            max_x = float('-inf')
            for i_exp, experiment_name in enumerate(exp_names):
                baseline = get_baseline(experiments[experiment_name].module)
                data = values[dataset_name][sequence_name][experiment_name]['rmse'].tolist()
                sorted_data = sorted(data)
                cumulated_vector = []
                for data_i in sorted_data:
                    count_smaller = bisect_left(sorted_data, 1.00001*data_i)
                    cumulated_vector.append(count_smaller)
                
                axs[j_seq].plot(sorted_data, cumulated_vector, marker='o', linestyle='-', color=baseline.color)
                min_x = min(min_x, min(sorted_data))
                max_x = max(max_x, max(sorted_data))

            y_max = experiments[exp_name].num_runs
            y_ticks = [0, y_max]

            width_x = 0.1*(max_x - min_x)
            min_x = 0# max(min_x - width_x,0)
            max_x = max_x + width_x
            x_ticks = [min_x, max_x]

            axs[j_seq].set_xticks(x_ticks)
            if j_seq == 0:
                axs[j_seq].set_yticks(y_ticks)
            else:
                axs[j_seq].set_yticklabels([])
            
            # Add minor ticks for the grid (every 10% of the axis range)
            axs[j_seq].xaxis.set_minor_locator(ticker.MultipleLocator(max_x / 4))
            axs[j_seq].yaxis.set_minor_locator(ticker.MultipleLocator(y_max / 4))

            axs[j_seq].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
            axs[j_seq].spines['top'].set_visible(False)   # Remove top border
            axs[j_seq].spines['right'].set_visible(False) # Remove right border
            axs[j_seq].tick_params(axis='both', which='minor', labelbottom=False, labelleft=False)
            axs[j_seq].tick_params(axis='y', labelsize=20, rotation=90) 
            axs[j_seq].tick_params(axis='x', labelsize=20, rotation=0)            
            axs[j_seq].set_xlim(x_ticks)
            axs[j_seq].set_ylim(y_ticks)

            axs[j_seq].tick_params(axis='x', pad=10) 
            axs[j_seq].set_xticklabels([f"{x_ticks[0]:.2f}", f"{x_ticks[1]:.2f}"], ha='right')  

            def set_format(tick):
                if tick == 0:
                    return f"0"
                return f"{tick:.1e}"
            
            axs[j_seq].set_xticklabels([set_format(tick) for tick in x_ticks])
            j_seq = j_seq + 1

    plot_name = os.path.join(comparison_path, f"{metric_name}_cummulated_error.pdf")
    plt.tight_layout()
    plt.savefig(plot_name, format='pdf')

    j_seq = 0
    for dataset_name, sequence_names in dataset_sequences.items():
        for i_seq, sequence_name in enumerate(sequence_names):
            axs[j_seq].set_title(dataset_nicknames[dataset_name][i_seq])

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles))
    plt.subplots_adjust(top=0.9, bottom=0.25)  # Adjust the top and bottom to make space for the legend
    plt.show(block=False)

def create_and_show_canvas(dataset_sequences, VSLAMLAB_BENCHMARK, comparison_path, padding=10):
    image_paths = []

    for dataset_name, sequence_names in dataset_sequences.items():
        for sequence_name in sequence_names:
            image_files = list_image_files_in_folder(
                os.path.join(VSLAMLAB_BENCHMARK, dataset_name.upper(), sequence_name, 'rgb'))
            image_paths.append(
                os.path.join(VSLAMLAB_BENCHMARK, dataset_name.upper(), sequence_name, 'rgb', image_files[0]))

    m = 5  # Number of columns
    n = math.ceil(len(image_paths) / m)  # Number of rows

    img_width = 640
    img_height = 480

    # Calculate canvas size including padding
    canvas_width = m * (img_width + padding) - padding
    canvas_height = n * (img_height + padding) - padding

    # Load and resize images
    images = [Image.open(path).resize((img_width, img_height), Image.LANCZOS) for path in image_paths]

    # Create a blank canvas with a white background
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')

    # Paste each image into the correct position with padding
    for i in range(n):
        for j in range(m):
            index = i * m + j
            if index < len(images):
                x_offset = j * (img_width + padding)
                y_offset = i * (img_height + padding)
                canvas.paste(images[index], (x_offset, y_offset))

    # Save the canvas
    plot_name = os.path.join(comparison_path, 'canvas_sequences.png')
    canvas.save(plot_name)

    # Show the canvas
    plt.figure(figsize=(12.8, 6.4))  # Convert pixels to inches for display
    plt.imshow(canvas)
    plt.axis('off')  # Hide the axis
    plt.show(block=False)

def num_tracked_frames(values, dataset_sequences, figures_path, experiments, shared_scale=False):
    # Get number of sequences
    num_sequences = 0
    splts = {}
    for dataset_name, sequence_names in dataset_sequences.items():
        dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
        for sequence_name in sequence_names:
            splts[sequence_name] = {}
            splts[sequence_name]['id'] = num_sequences
            splts[sequence_name]['dataset_name'] = dataset_name
            splts[sequence_name]['nickname']= dataset.get_sequence_nickname(sequence_name)
            num_sequences += 1

    exp_names = list(experiments.keys())

    # Figure dimensions
    NUM_COLS = 5
    NUM_ROWS = math.ceil(num_sequences / NUM_COLS)
    XSIZE, YSIZE = 12, 2 * NUM_ROWS + 0.5
    WIDTH_PER_SERIES = min(XSIZE / len(exp_names), 1.0)/3
    FONT_SIZE = 15
    fig, axs = plt.subplots(NUM_ROWS, NUM_COLS, figsize=(XSIZE, YSIZE))
    axs = axs.flatten()

    # Create legend handles
    legend_handles = []
    colors = {}
    for i_exp, exp_name in enumerate(exp_names):
        baseline = get_baseline(experiments[exp_name].module)   
        colors[exp_name] = baseline.color
        legend_handles.append(Patch(color=colors[exp_name], label=exp_names[i_exp]))

    # Plot boxplots        
    max_rgb = {}      
    for sequence_name, splt in splts.items():
        for i_exp, exp_name in enumerate(exp_names):
            values_seq_exp = values[splt['dataset_name']][sequence_name][exp_name]
            if values_seq_exp.empty:
                max_rgb[sequence_name] = 1
            else:
                num_frames = values[splt['dataset_name']][sequence_name][exp_name]['num_frames']
                max_rgb[sequence_name] = max(num_frames)

    for sequence_name, splt in splts.items():
        for i_exp, exp_name in enumerate(exp_names):
            values_seq_exp = values[splt['dataset_name']][sequence_name][exp_name]    
            if values_seq_exp.empty:
                continue

            num_frames = values_seq_exp['num_frames'] 
            num_tracked_frames = values_seq_exp['num_tracked_frames'] 
            num_evaluated_frames = values_seq_exp['num_evaluated_frames']   
         
            if shared_scale:
                num_frames /= max_rgb[sequence_name]
                num_tracked_frames /= max_rgb[sequence_name]
                num_evaluated_frames /= max_rgb[sequence_name]

            median_num_frames = np.median(num_frames)
            median_num_tracked_frames = np.median(num_tracked_frames)
            median_num_evaluated_frames = np.median(num_evaluated_frames)

            positions = np.array([3 * i_exp, 3 * i_exp + 1, 3 * i_exp + 2]) * WIDTH_PER_SERIES
            axs[splt['id']].bar(
            positions, 
            [median_num_frames, median_num_tracked_frames, median_num_evaluated_frames], 
            color=colors[exp_name], alpha=0.3, width=WIDTH_PER_SERIES*0.9)
            
            metrics = [num_frames, num_tracked_frames, num_evaluated_frames]
            boxprops = medianprops = whiskerprops = capprops = dict(color=colors[exp_name])
            flierprops = dict(marker='o', color=colors[exp_name], alpha=1.0)    
            for i, metric in enumerate(metrics):
                positions = [(3 * i_exp + i) * WIDTH_PER_SERIES]
                boxplot_accuracy = axs[splt['id']].boxplot(
                    metrics[i],
                    positions=positions, widths=WIDTH_PER_SERIES,
                    patch_artist=False,
                    boxprops=boxprops, medianprops=medianprops,
                    whiskerprops=whiskerprops,
                    capprops=capprops, flierprops=flierprops)
        
        if shared_scale:
            yticks = [0, 1]
        else:
            yticks = [0, max_rgb[sequence_name]]
        axs[splt['id']].grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        axs[splt['id']].set_xticklabels([])
        axs[splt['id']].set_ylim(yticks)
        axs[splt['id']].tick_params(axis='y', labelsize=FONT_SIZE) 
        axs[splt['id']].yaxis.set_minor_locator(ticker.MultipleLocator(max_rgb[sequence_name] / 4))
        axs[splt['id']].set_yticks(yticks)
        if not shared_scale:    
            axs[splt['id']].set_yticks(yticks)
            tick_labels = axs[splt['id']].get_yticklabels() 
            tick_labels[0].set_transform(tick_labels[0].get_transform() + ScaledTranslation(0.2, -0.15, fig.dpi_scale_trans))
            tick_labels[1].set_transform(tick_labels[1].get_transform() + ScaledTranslation(0.5, +0.15, fig.dpi_scale_trans))
        else:
            if splt['id'] == 0:
                axs[splt['id']].set_yticks(yticks)
            else:
                axs[splt['id']].set_yticks([])   

    plt.tight_layout()
    plot_name = os.path.join(figures_path, f"num_frames_boxplot_paper.pdf")
    if shared_scale:
        plot_name = plot_name.replace(".pdf", "_shared_scale.pdf")
    plt.savefig(plot_name, format='pdf')

    # Adjust plot properties for display
    for sequence_name, splt in splts.items():
        if shared_scale:
            axs[splt['id']].set_title(splt['nickname'], fontsize=FONT_SIZE,  fontweight='bold')
        else:
            axs[splt['id']].set_title(splt['nickname'], fontsize=FONT_SIZE, fontweight='bold', pad=30)

    fig.legend(handles=legend_handles, loc='lower center', ncol=len(legend_handles), fontsize=FONT_SIZE)
    
    if shared_scale:
        plt.tight_layout(rect=[0, 0.15, 1, 0.95])
    else:
        fig.set_size_inches(XSIZE, 2*YSIZE)
        plt.tight_layout(rect=[0, 0.10, 1, 0.95])

    plot_name = os.path.join(figures_path, f"num_frames_boxplot.pdf")
    if shared_scale:
        plot_name = plot_name.replace(".pdf", "_shared_scale.pdf")
    plt.savefig(plot_name, format='pdf')

    fig.canvas.manager.set_window_title("Number of Frames")
    plt.show(block=False)

