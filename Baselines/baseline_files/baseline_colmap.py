from pathlib import Path

from Baselines.BaselineVSLAMLAB import BaselineVSLAMLAB

SCRIPT_LABEL = f"\033[95m[{Path(__file__).name}]\033[0m "


class COLMAP_baseline(BaselineVSLAMLAB):
    """colmap helper for VSLAM-LAB Baselines (entry point: Baselines/colmap/vslamlab_colmap.py)."""

    def __init__(self, baseline_name: str = 'colmap', baseline_folder: str = 'colmap') -> None:

        # matcher_type: 'exhaustive' | 'sequential' (sequential with loop detection; the vocabulary
        # tree for the feature type is COLMAP's default, auto-downloaded once into ~/.cache/colmap).
        # matching_type: feature extraction + matching pair (Baselines/colmap/colmap_matcher.py):
        # sift_bruteforce | sift_lightglue | aliked_bruteforce | aliked_lightglue | loma_b_bruteforce |
        # loma_b_loma | loma_b_loma_r | loma_b_loma_l | loma_b_loma_g | loma_b128_bruteforce | loma_b128_loma.
        # ALIKED / LoMa / LightGlue are ONNX models COLMAP downloads once into ~/.cache/colmap (as are the
        # vocabulary trees of matcher_type: sequential); `pixi run download-colmap-models` pre-fetches them
        # for nodes without internet.
        # use_mask: 1 -> feature extraction honours the rgb csv's path_mask_<i> column when the run
        # pipeline provides one ('segmentation: mask2former', 'refraction: refrax', datasets that
        # ship masks); 0 -> masks ignored (see Baselines/colmap/colmap_matcher.py).
        # optimize_intrinsics: 1 -> bundle adjustment refines the camera intrinsics (focal length and
        # distortion; the principal point stays fixed, as in COLMAP's default); 0 -> the intrinsics
        # from the calibration yaml are kept fixed. Ignored (forced to 1) when the calibration model
        # is 'unknown', since there are no intrinsics to keep (see Baselines/colmap/colmap_mapper.py).
        # camera_model: COLMAP camera model for an 'unknown' calibration, e.g. 'PINHOLE' to estimate focal lengths
        # without distortion ('' -> OPENCV); a known calibration sets its own model.
        # dense: 1 -> after the sparse model and trajectory are written, run COLMAP's dense pipeline
        # (image_undistorter -> patch_match_stereo -> stereo_fusion) on the best sub-model, into
        # <exp_folder>/colmap_<id>/dense/ with the fused cloud copied to <exp_folder>/<id>_dense.ply.
        # Needs the CUDA colmap build (linux-64 / win-64 in pixi.toml) and use_gpu=1; otherwise, or if a
        # dense command fails, it is skipped with a warning and the run still succeeds (see
        # Baselines/colmap/colmap_dense.py).
        # dense_max_image_size: longest image side used for undistortion / patch match / fusion
        # (COLMAP presets: 1000 low, 1600 medium, -1 high = full resolution).
        # mesher: 'none' | 'delaunay' | 'poisson' | 'advancing_front' -> mesh the fused cloud / dense
        # workspace, copied to <id>_mesh.ply.
        # Fork additions (Baselines/colmap is the fork of COLMAP-VSLAM-LAB that holds the hybrid matcher):
        # matcher_type: 'hybrid' -> exhaustive SIFT + learned-feature matches on selected pairs (Baselines/colmap/hybrid_matcher.py),
        #   then `colmap geometric_verifier`. Its options:
        #   hybrid_features: 'superpoint' | 'aliked' (4 rotations) | 'sift' (rotation invariant, 1)
        #   hybrid_matching: 'lightglue' | 'bruteforce' (mutual nearest neighbours; + ratio test 0.8 for sift)
        #   pair_selection: 'vpr' (MegaLoc pairs) | 'cross_session' | 'all'
        #   vpr_matrix / vpr_rgb_csv: distance matrix and the rgb csv its rows follow ('' -> <sequence>/vpr-lab/D.npy
        #     and <sequence>/rgb.csv; relative paths are inside the sequence folder)
        #   vpr_threshold: kept if min-max-normalised distance <= threshold; lg_min_matches: hybrid matches kept if > this;
        #   min_matches: pair dropped below this; verification: 'colmap' | 'glomap' (GLOMAP 1.2.0-like) | 'none' (original pipeline)
        # single_camera_per_folder: 1 (upstream) -> one camera per image folder; 0 -> one shared camera (original hybrid
        #   pipeline). COLMAP does not follow symlinks, so a combined multi-session sequence gets one camera either way.
        # per_session_calibration: 1 -> one camera per session of a combined sequence, each with its own session
        #   sequence's calibration.yaml (needs a known calibration.yaml in every session and in the combined sequence)
        # random_seed: -1 (COLMAP default) or >= 0 for repeatable verification + mapping
        # init_pair: 'colmap' (COLMAP chooses) or 'cross_session' (the verified cross-session pair with the most matches;
        #   learned keypoints are matched only across sessions, so a model started inside one session can fragment)
        default_parameters = {'verbose': 1, 'mode': 'mono', 'matcher_type': 'exhaustive',
                             'matching_type': 'sift_bruteforce', 'mapper_type': 'colmap', 'rgb_max': 50000000,
                             'use_mask': 0, 'optimize_intrinsics': 1, 'camera_model': '',
                             'dense': 0, 'dense_max_image_size': 1600, 'mesher': 'none',
                             'single_camera_per_folder': 1, 'per_session_calibration': 0, 'random_seed': -1,
                             'hybrid_features': 'superpoint', 'hybrid_matching': 'lightglue',
                             'pair_selection': 'vpr', 'vpr_matrix': '', 'vpr_rgb_csv': '', 'vpr_threshold': 0.5,
                             'lg_min_matches': 40, 'min_matches': 10, 'verification': 'colmap',
                             'init_pair': 'colmap'}

        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder, default_parameters)
        self.color = (0.800, 0.400, 0.750)
        self.modes = ['mono']
        self.cam_models = ['unknown', 'pinhole', 'radtan4', 'radtan5', 'radtan8', 'equid4']
        self.command_style = 'python'
