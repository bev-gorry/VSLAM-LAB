#!/bin/bash
# Writes the flat-reconstruction cameras (calib_grid: fixed OPENCV, f 565, principal point at the image centre) into a
# freshly downloaded Sesoko benchmark, so per_session_calibration finds a known camera for every session.
#   2016 / 2017: k1 -0.1325    2018: k1 -0.026
# Per-session calibration follows a combined sequence's symlinks to the end (sskall-s05 -> ssk16-s05 -> ssk16), so the
# cameras go into the full-year folders ssk16/17/18. Every sequence an experiment runs on needs a known camera too:
#   ssk1X-full, ssk1X-s01..s05   single-year runs (the per-session runs): the mapper refines an 'unknown' camera
#   sskall-full, sskall-s01..s05 joint runs: per_session_calibration refuses an 'unknown' combined sequence; they get
#                                the 2016/2017 camera, while each session still uses its own year's camera.
# The downloaded 'unknown' calibration.yaml of each folder is kept as calibration_unknown.yaml and used as the template.
#
# Usage (from the VSLAM-LAB root):  bash scripts/set_sesoko_cameras.sh
set -euo pipefail

B=$(pixi run --frozen -e vslamlab python -c "from path_constants import VSLAMLAB_BENCHMARK; print(VSLAMLAB_BENCHMARK)")/SESOKO

write() {  # <sequence> <k1> <comment>
  local dir=$B/$1
  [ -d "$dir" ] || { echo "$1: not downloaded, skipped"; return 0; }
  [ -f "$dir/calibration_unknown.yaml" ] || cp "$dir/calibration.yaml" "$dir/calibration_unknown.yaml"
  grep -q "cam_model: unknown" "$dir/calibration_unknown.yaml" || { echo "$1: calibration_unknown.yaml is not 'unknown'"; exit 1; }
  sed -e "s|^---$|---\n# $3|" \
      -e "s|cam_model: unknown,|cam_model: pinhole,\n     distortion_type: radtan4,|" \
      -e "s|focal_length: \[0.0, 0.0\],|focal_length: [565.0, 565.0],|" \
      -e "s|principal_point: \[0.0, 0.0\],|principal_point: [304.0, 252.5],\n     distortion_coefficients: [$2, 0.0, 0.0, 0.0],|" \
      "$dir/calibration_unknown.yaml" > "$dir/calibration.yaml"
  echo "$1: OPENCV f 565, k1 $2"
}

SUBSETS="s01 s02 s03 s04 s05"
for year in ssk16 ssk17; do
  for seq in "$year" "$year-full" $(for s in $SUBSETS; do echo "$year-$s"; done); do
    write "$seq" -0.1325 "Flat-reconstruction intrinsics from calib_grid: 2016/2017 camera"
  done
done
for seq in ssk18 ssk18-full $(for s in $SUBSETS; do echo "ssk18-$s"; done); do
  write "$seq" -0.026 "Flat-reconstruction intrinsics from calib_grid: 2018 camera"
done
for seq in sskall-full $(for s in $SUBSETS; do echo "sskall-$s"; done); do
  write "$seq" -0.1325 "Joint sequence: the 2016/2017 camera; per_session_calibration uses each session's own camera"
done
