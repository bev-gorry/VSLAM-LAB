import os.path

from Baselines.BaselineVSLAMLab import BaselineVSLAMLab

from utilities import VSLAMLAB_BASELINES
class MONOGS_baseline(BaselineVSLAMLab):
    def __init__(self, baselines_path):
        baseline_name = 'monogs'
        baseline_folder = 'MonoGS'
        baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        default_parameters = [f'config:{os.path.join(baseline_path, 'configs', 'mono', 'vslamlab', 'vslamlab.yaml')}', 'verbose:1']

        # Initialize the baseline
        super().__init__(baseline_name, baselines_path)
        self.label = f"\033[96m{baseline_name}\033[0m"
        self.baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        self.default_parameters = default_parameters


