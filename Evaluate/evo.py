import os
import subprocess
import zipfile
import pandas as pd
from sklearn.covariance import EllipticEnvelope
import numpy as np


def evo_ape_zip(groundtruth_file, trajectory_file, evaluation_folder, max_time_difference=0.1):
    traj_file_name = os.path.basename(trajectory_file).replace(".txt", "")
    traj_zip = os.path.join(evaluation_folder, f"{traj_file_name}.zip")
    if os.path.exists(traj_zip):
        return

    command = (f"pixi run -e evo evo_ape tum {groundtruth_file} {trajectory_file} -va -as "
               f"--t_max_diff {max_time_difference} --save_results {traj_zip}")
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with zipfile.ZipFile(traj_zip, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.endswith(trajectory_file + '.tum'):
                with zip_ref.open(file_name) as source_file:
                    destination_file_path = os.path.join(evaluation_folder,
                                                         os.path.basename(file_name).replace(".txt", ""))
                    with open(destination_file_path, 'wb') as target_file:
                        target_file.write(source_file.read())
                break

    df = pd.read_csv(destination_file_path, delimiter=' ', header=None)
    df.columns = ['ts', 'tx', 'ty', 'tz', 'qx', 'qy', 'qz', 'qw']
    df = df.sort_values(by='ts')
    df.to_csv(destination_file_path, index=False)

    gt_file = os.path.join(evaluation_folder, 'gt.tum')
    if os.path.exists(gt_file):
        return

    with zipfile.ZipFile(traj_zip, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.endswith(groundtruth_file + '.tum'):
                with zip_ref.open(file_name) as source_file:
                    destination_file_path = gt_file
                    with open(destination_file_path, 'wb') as target_file:
                        target_file.write(source_file.read())
                break

    df = pd.read_csv(gt_file, delimiter=' ', header=None)
    df.columns = ['ts', 'tx gt', 'ty gt', 'tz gt', 'qx gt', 'qy gt', 'qz gt', 'qw gt']
    df = df.sort_values(by='ts')
    df.to_csv(gt_file, index=False)

def evo_get_accuracy(evaluation_folder):
    accuracy_raw = os.path.join(evaluation_folder, 'accuracy_raw.csv')
    if os.path.exists(accuracy_raw):
        os.remove(accuracy_raw)

    command = (f"pixi run -e evo evo_res {os.path.join(evaluation_folder, "*.zip")} --save_table {accuracy_raw}")
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    df = pd.read_csv(accuracy_raw)
    df = df.rename(columns={df.columns[0]: 'traj_name'})
    data = df['rmse'].dropna()
    data_reshaped = data.values.reshape(-1, 1)

    # Count the number of lines
    keyframe_traj_files = [f for f in os.listdir(evaluation_folder) if '_KeyFrameTrajectory.tum' in f]
    keyframe_traj_files.sort()
    for keyframe_traj_file in keyframe_traj_files:
        with open(os.path.join(evaluation_folder, keyframe_traj_file), 'r') as file:
            traj_name = keyframe_traj_file.replace('.tum', '.txt')
            num_evaluation_points = sum(1 for line in file)
            df.loc[df['traj_name'] == traj_name, 'Number of Evaluation Points'] = num_evaluation_points

    # Use EllipticEnvelope to fit the data
    num_traj_files = len(keyframe_traj_files)
    if num_traj_files > 5000:
        outlier_detector = EllipticEnvelope(contamination=0.10)  # 5% contamination is typical
        outliers = outlier_detector.fit_predict(data_reshaped)
        outlier_indices = np.where(outliers == -1)[0]
        cleaned_df = df.drop(index=outlier_indices)
    else:
        outlier_indices = []
        cleaned_df = df

    accuracy = os.path.join(evaluation_folder, 'accuracy.csv')
    if os.path.exists(accuracy):
        os.remove(accuracy)
    cleaned_df.to_csv(accuracy, index=False)

    outlier_file_names = df.iloc[outlier_indices].iloc[:, 0]
    for outlier_file_name in outlier_file_names:
        traj_file = os.path.join(evaluation_folder, f"{outlier_file_name.replace(".txt", "")}.tum")
        if(os.path.exists(traj_file)):
            os.remove(traj_file)
