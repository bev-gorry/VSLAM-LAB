import os.path

from Baselines.BaselineVSLAMLab import BaselineVSLAMLab

from utilities import VSLAMLAB_BASELINES


class ANYFEATURE_baseline(BaselineVSLAMLab):
    def __init__(self, baselines_path):
        baseline_name = 'anyfeature'
        baseline_folder = 'AnyFeature-VSLAM'
        baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        default_parameters = ['Vis:1', 'Feat:orb32', f'anyfeat:{baseline_path}/']

        # Initialize the baseline
        super().__init__(baseline_name, baselines_path)
        self.label = f"\033[96m{baseline_name}\033[0m"
        self.baseline_path = baseline_path
        self.default_parameters = default_parameters
