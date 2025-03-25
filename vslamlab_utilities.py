import sys, os, yaml, shutil, csv
import pandas as pd
from inputimeout import inputimeout, TimeoutOccurred

from Datasets.get_dataset import get_dataset
from Baselines.baseline_utilities import get_baseline
from utilities import ws, check_yaml_file_integrity, print_msg
from path_constants import VSLAMLAB_BENCHMARK, VSLAMLAB_EVALUATION, VSLAM_LAB_DIR, CONFIG_DEFAULT

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "

class Experiment:
    def initialize(self, name, settings):
        self.name = name
        self.folder = os.path.join(VSLAMLAB_EVALUATION, self.name)
        self.num_runs = settings.get('NumRuns', 1)
        self.module = settings.get('Module', "default")
        self.parameters = settings['Parameters']

        self.log_csv = os.path.join(self.folder, 'vslamlab_exp_log.csv')
        self.config_yaml = os.path.join(VSLAM_LAB_DIR, 'configs', settings.get('Config', CONFIG_DEFAULT))
        self.ablation_csv = settings.get('Ablation', None)

    def __init__(self, name, settings):            
        self.initialize(name, settings)
        if os.path.exists(self.log_csv):
            exp_log = pd.read_csv(self.log_csv)
            new_runs = []
            with open(self.config_yaml, 'r') as file:
                config_file_data = yaml.safe_load(file)
                for i in range(self.num_runs):
                    for dataset_name, sequence_names in config_file_data.items():
                        for sequence_name in sequence_names:
                            exp_it = str(i).zfill(5)  
                            exp_log_row = exp_log[(exp_log["method_name"] == self.module) 
                                                & (exp_log["dataset_name"] == dataset_name) 
                                                & (exp_log["sequence_name"] == sequence_name) 
                                                & (exp_log["exp_it"] == int(exp_it))]
                            if exp_log_row.empty:
                                new_run = [self.module, dataset_name, sequence_name, f"{exp_it}", "", "",0.0, 0.0, "", "none"]
                                new_runs.append(new_run)
            with open(self.log_csv, mode="a", newline="") as file:
                writer = csv.writer(file)
                for new_run in new_runs:
                    writer.writerow(new_run)
        else: 
            log_headers = ["method_name", "dataset_name", "sequence_name", "exp_it", "STATUS", "SUCCESS", "TIME", "MEMORY", "COMMENTS", "EVALUATION"]

            with open(self.log_csv, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(log_headers)
                with open(self.config_yaml, 'r') as file:
                    config_file_data = yaml.safe_load(file)
                    for i in range(self.num_runs):
                        for dataset_name, sequence_names in config_file_data.items():
                            for sequence_name in sequence_names:
                                exp_it = str(i).zfill(5)  
                                writer.writerow([self.module, dataset_name, sequence_name, f"{exp_it}", "", "",0.0, 0.0, "", "none"])

def check_experiments(exp_yaml, overwrite):

    check_yaml_file_integrity(exp_yaml)
    with open(exp_yaml, 'r') as file:
        exp_data = yaml.safe_load(file)

    print(f"{SCRIPT_LABEL}Experiment summary: {exp_yaml}")
    for exp_name in exp_data.keys():
        print(f"{ws(4)} - {exp_name}")  
    
    # Check experiment syntax
    check_experiment_baseline_names(exp_data, exp_yaml)
    check_experiment_sequence_names(exp_data)

    # Check experiment resources
    num_baselines_to_install, num_automatic_install, baselines_to_install = check_experiment_baselines_installed(exp_data)
    num_download_issues, num_automatic_download, sequences_to_download = check_experiment_sequences_available(exp_data, exp_yaml)
    check_experiment_resources(num_baselines_to_install, num_automatic_install, num_download_issues, num_automatic_download)

    # Check experiment runs
    experiments = check_experiment_runs(exp_data, overwrite)

    # Get experiment resources
    install_experiment_baselines(baselines_to_install)
    download_experiment_sequences(sequences_to_download)

    return experiments

###################### Get experiment resources ######################
def download_experiment_sequences(sequences_to_download):
    first_time = True
    for dataset_name, sequence_names in sequences_to_download.items():
        dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
        for sequence_name in sequence_names:
            if first_time:
                print(f"\n{SCRIPT_LABEL}Downloading (to {VSLAMLAB_BENCHMARK}) ...")
                first_time = False
            dataset.download_sequence(sequence_name)

def install_experiment_baselines(baselines_to_install):
    for baseline_name in baselines_to_install:
        baseline = get_baseline(baseline_name)
        baseline.git_clone()
        baseline.install()

###################### Check experiment runs ######################
def check_experiment_runs(exp_data, overwrite = False):
    experiments = {}
    for exp_name, settings in exp_data.items():
        exp_folder = os.path.join(VSLAMLAB_EVALUATION, exp_name)
        exp_log_csv = os.path.join(exp_folder, 'vslamlab_exp_log.csv')

        if overwrite or not os.path.exists(exp_log_csv):
            if os.path.exists(exp_folder):
                shutil.rmtree(exp_folder)

        os.makedirs(exp_folder, exist_ok=True)
        experiments[exp_name] = Experiment(exp_name, settings)

    return experiments

###################### Check experiment resources ######################
def check_experiment_baselines_installed(exp_data):
    print_msg(f"\n{SCRIPT_LABEL}", f"Checking experiment baselines:", verb='LOW')
    baselines = {}
    for exp_name, settings in exp_data.items():
        baselines[settings.get('Module')] = exp_name

    num_baselines_to_install = 0
    baselines_to_install = []
    for baseline_name, exp_name in baselines.items():
        baseline = get_baseline(baseline_name)
        if baseline.is_installed():
            print_msg(f"{ws(4)}", f"- {baseline.label}:\033[92m installed\033[0m", verb='LOW')
        else:    
            print_msg(f"{ws(4)}", f"- {baseline.label}:\033[93m not installed\033[0m \033[92m (automatic install)\033[0m", verb='LOW')
            num_baselines_to_install += 1
            baselines_to_install.append(baseline_name)

    return num_baselines_to_install, num_baselines_to_install, baselines_to_install


def check_experiment_sequences_available(exp_data, exp_yaml):
    print_msg(f"\n{SCRIPT_LABEL}", f"Checking experiment sequences:", verb='LOW')
    with open(exp_yaml, 'r') as file:
        experiment_data = yaml.safe_load(file)  

    configs = {}
    for exp_name, settings in experiment_data.items():
        configs[settings.get('Config')] = exp_name  

    sequences = {}
    for config_yaml, exp_name in configs.items():
        config_file = os.path.join(VSLAM_LAB_DIR, 'configs', config_yaml)
        with open(config_file, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names: 
                    sequences[sequence_name] = dataset_name
    
    # Check sequence availability
    sequences_to_download = {}
    num_total_sequences = len(sequences)
    num_available_sequences = 0
    for sequence_name, dataset_name in sequences.items():
        dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
        if dataset_name not in sequences_to_download:
            sequences_to_download[dataset_name] = []
        if dataset.check_sequence_availability(sequence_name) == "available":
            print_msg(f"{ws(4)}", f"- {dataset.dataset_label} {dataset.dataset_color}{sequence_name}:\033[92m available\033[0m", verb='MEDIUM')
            num_available_sequences += 1
        else:
            print_msg(f"{ws(4)}", f"- {dataset.dataset_label} {dataset.dataset_color}{sequence_name}:\033[93m not available\033[0m \033[92m (automatic download)\033[0m", verb='MEDIUM')
            sequences_to_download[dataset_name].append(sequence_name)
    print_msg(f"{ws(4)}", f"- Sequences available: \033[92m{num_available_sequences}\033[0m / {num_total_sequences}", verb='LOW')
    if num_available_sequences < num_total_sequences:
        print_msg(f"{ws(4)}", f"- Sequences to download: \033[93m{num_total_sequences - num_available_sequences}\033[0m / {num_total_sequences}", verb='LOW')

    # Check download issues
    num_download_issues = 0
    num_automatic_solution = 0
    for dataset_name, sequence_names in sequences_to_download.items():
        if sequence_names == []:
            continue
        dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
        issues_seq = dataset.get_download_issues()
        for issue_seq in issues_seq:
            print_msg(f"\n{ws(4)}", f"[{dataset_name}][{issue_seq['name']}]: {issue_seq['description']}",'warning')
            print(f"{ws(8)}[{issue_seq['mode']}]: {issue_seq['solution']}")
            num_download_issues += 1
            if issue_seq['mode'] == '\033[92mautomatic download\033[0m':
                num_automatic_solution += 1

    return num_download_issues, num_automatic_solution, sequences_to_download


def check_experiment_resources(num_baselines_to_install, num_automatic_install, num_download_issues, num_automatic_download):
    if num_baselines_to_install > 0 or num_download_issues > 0:
        print_msg(f"\n{SCRIPT_LABEL}",f"Your experiments have {num_baselines_to_install} install issues and {num_download_issues} download issues:",'warning')
        if(num_baselines_to_install - num_automatic_install) > 0:
            print_msg(f"{ws(4)}",f"- {num_baselines_to_install - num_automatic_install} baselines need to be installed manually.",'warning')
            print_msg(f"{ws(4)}", f"Some issues are  not automatically fixable. Please, fix them manually and run the experiment again.",'error')
            exit(1)
        if num_download_issues - num_automatic_download > 0:
            print_msg(f"{ws(4)}", f"Some issues are  not automatically fixable. Please, fix them manually and run the experiment again.",'error')
            exit(1)
        
        message = (f"{ws(4)}All issues are \033[92mautomatically\033[0m fixable. Would you like to continue solving them (Y/n): ")
        try:
            user_input = inputimeout(prompt=message, timeout=60*10).strip().upper()
        except TimeoutOccurred:
            user_input = 'Y'
            print(f"{ws(4)}No input detected. Defaulting to 'Y'.")
        if user_input != 'Y':
            exit()   

###################### Check experiment syntax ######################
def check_experiment_baseline_names(exp_data, exp_yaml=''):
    baselines = {}
    for exp_name, settings in exp_data.items():
        baselines[settings.get('Module')] = exp_name

    for baseline_name, exp_name in baselines.items():
        baseline = get_baseline(baseline_name)
        if baseline == "Invalid case":
            print_msg(f"\n{SCRIPT_LABEL}", f"Checking experiment baseline names (in '{exp_yaml}'):",'info')
            print_msg(f"{ws(4)}",f"[Error] 'Module: {baseline_name}' baseline in '{exp_name}' doesn't exist.",'error')
            print_baselines()
            sys.exit(1)

def check_experiment_sequence_names(exp_data):

    # List config.yaml files
    configs = {}
    for exp_name, settings in exp_data.items():
        configs[settings.get('Config')] = exp_name  

    # Check config.yaml integrity, dataset and sequence existence
    dataset_list = list_datasets()
    for config_yaml, exp_name in configs.items():

        # Check config.yaml integrity
        config_file = os.path.join(VSLAM_LAB_DIR, 'configs', config_yaml)
        check_yaml_file_integrity(config_file) 
        
        with open(config_file, 'r') as file:
            config_file_data = yaml.safe_load(file)

            # Check dataset existence
            for dataset_name, sequence_names in config_file_data.items():
                if not (dataset_name in dataset_list): 
                    print_msg(f"\n{SCRIPT_LABEL}", f"Checking experiment dataset names (in '{config_file}'):",'info')
                    print_msg(f"{ws(4)}", f"[Error] Dataset '{dataset_name}' doesn't exist.",'error')
                    print_datasets()
                    sys.exit(1)

                # Check sequence existence
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names: 
                    if not dataset.contains_sequence(sequence_name):
                        print_msg(f"\n{SCRIPT_LABEL}", f"Checking experiment sequence names (in '{config_file}'):",'info')
                        print_msg(f"{ws(4)}", f"[Error] Sequence '{sequence_name}' in Dataset '{dataset_name}' doesn't exist.",'error')
                        print(f"\nAvailable sequences are: {dataset.sequence_names}")
                        sys.exit(1)

def list_datasets():
    dataset_scripts_path = os.path.join(VSLAM_LAB_DIR, 'Datasets')
    dataset_scripts = []
    for filename in os.listdir(dataset_scripts_path):
        if 'dataset_' in filename and filename.endswith('.yaml') and 'utilities' not in filename:
            dataset_scripts.append(filename)

    dataset_scripts = [item.replace('dataset_', '').replace('.yaml', '') for item in dataset_scripts]

    return dataset_scripts

def list_baselines():
    baseline_scripts_path = os.path.join(VSLAM_LAB_DIR, 'Baselines')
    baseline_scripts = []
    for filename in os.listdir(baseline_scripts_path):
        if 'baseline_' in filename and filename.endswith('.py') and 'utilities' not in filename:
            baseline_scripts.append(filename)

    baseline_scripts = [item.replace('baseline_', '').replace('.py', '') for item in baseline_scripts]

    return baseline_scripts

def baseline_info(baseline_name):
    baseline = get_baseline(baseline_name)
    baseline.info_print()

def print_datasets():
    dataset_list = list_datasets()
    print(f"\n{SCRIPT_LABEL}Accessible datasets in VSLAM-LAB:")
    for dataset in dataset_list:
        print(f" - {dataset}")
    print("")

def print_baselines():
    baseline_list = list_baselines()
    print(f"\n{SCRIPT_LABEL}Accessible baselines in VSLAM-LAB:")
    for baseline in baseline_list:
        print(f" - {baseline}")
    print("For detailed information about a baseline, use 'pixi run baseline-info <baseline_name>'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        function_name = sys.argv[1]
        if function_name == "baseline_info":
            baseline_info(sys.argv[2])
        if function_name == "print_datasets":
            print_datasets()
        if function_name == "print_baselines":
            print_baselines()
            