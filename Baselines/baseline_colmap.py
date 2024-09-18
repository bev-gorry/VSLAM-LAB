import os.path

from Baselines.BaselineVSLAMLab import BaselineVSLAMLab

from utilities import VSLAMLAB_BASELINES


class COLMAP_baseline(BaselineVSLAMLab):
    def __init__(self, baselines_path):
        baseline_name = 'colmap'
        baseline_folder = 'colmap'
        baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        default_parameters = ['verbose:1', 'matcher_type:sequential', 'use_gpu:1', 'max_rgb:50']

        # Initialize the baseline
        super().__init__(baseline_name, baselines_path)
        self.label = f"\033[96m{baseline_name}\033[0m"
        self.baseline_path = baseline_path
        self.default_parameters = default_parameters
