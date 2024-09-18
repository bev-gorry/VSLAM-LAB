import os.path

from Baselines.BaselineVSLAMLab import BaselineVSLAMLab

from utilities import VSLAMLAB_BASELINES
class GLOMAP_baseline(BaselineVSLAMLab):
    def __init__(self, baselines_path):
        baseline_name = 'glomap'
        baseline_folder = 'glomap'
        baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        default_parameters = [f'verbose:1', f'matcher_type:sequential', 'use_gpu: use_gpu:1', 'max_rgb:50',
                              'settings_yaml: settings_yaml:Baselines/glomap/glomap_settings.yaml']

        # Initialize the baseline
        super().__init__(baseline_name, baselines_path)
        self.label = f"\033[96m{baseline_name}\033[0m"
        self.baseline_path = baseline_path
        self.default_parameters = default_parameters