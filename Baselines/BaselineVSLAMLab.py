
class BaselineVSLAMLab:

    def __init__(self, baseline_name, baselines_path):
        self.baseline_name = baseline_name
        self.baselines_path = baselines_path
        self.default_parameters = ''

    def get_default_parameters(self):
        return self.default_parameters
