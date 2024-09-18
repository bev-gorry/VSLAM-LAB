import os.path

from Baselines.BaselineVSLAMLab import BaselineVSLAMLab

from utilities import VSLAMLAB_BASELINES


class ORBSLAM2_baseline(BaselineVSLAMLab):
    def __init__(self, baselines_path):
        baseline_name = 'orbslam2'
        baseline_folder = 'ORB_SLAM2'
        baseline_path = os.path.join(VSLAMLAB_BASELINES, baseline_folder)
        default_parameters = [f'Vis:1', f'Voc:{os.path.join(baseline_path, 'Vocabulary')}']

        # Initialize the baseline
        super().__init__(baseline_name, baselines_path)
        self.label = f"\033[96m{baseline_name}\033[0m"
        self.baseline_path = baseline_path
        self.default_parameters = default_parameters
