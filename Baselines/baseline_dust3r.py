import os.path

from Baselines.BaselineVSLAMLab import BaselineVSLAMLab

from utilities import VSLAMLAB_BASELINES
class DUST3R_baseline(BaselineVSLAMLab):
    def __init__(self, baselines_path):
        baseline_name = 'dust3r'
        baseline_folder = 'dust3r'
        baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        default_parameters = ['-v']

        # Initialize the baseline
        super().__init__(baseline_name, baselines_path)
        self.label = f"\033[96m{baseline_name}\033[0m"
        self.baseline_path = baseline_path
        self.default_parameters = default_parameters
