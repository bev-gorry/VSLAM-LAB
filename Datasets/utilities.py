import csv
import os


def initialize_log_run_sequence_time(csv_path):
    if not os.path.exists(csv_path):
        with open(csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['experiment_id', 'runtime'])  # Write the header


def append_to_log_run_sequence_time(csv_path, experiment_id, run_time):
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([experiment_id, run_time])


def log_run_sequence_time(exp_folder, experiment_id, run_time):
    csv_path = os.path.join(exp_folder, 'log_run_sequence_time.csv')
    initialize_log_run_sequence_time(csv_path)
    append_to_log_run_sequence_time(csv_path, experiment_id, run_time)
