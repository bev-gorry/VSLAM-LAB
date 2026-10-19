#!/bin/bash
# Brute-force search over fixed camera intrinsics: for every grid point, write the camera into the sequences'
# calibration.yaml, run COLMAP with fixed intrinsics, evaluate against the AUV navigation, then summarise
# (planarity + ATE) over all points. Original calibration.yaml files are restored on exit, even after an error.
# Completed experiments are skipped, so an interrupted grid resumes where it stopped.
#
# Usage (from the VSLAM-LAB root):  bash calib_grid/run_calib_grid.sh calib_grid/grid_sesoko_half.yaml
set -euo pipefail

GRID=${1:?usage: $0 <grid.yaml>}
HELPER="pixi run -e vslamlab python calib_grid/calib_grid.py"

mapfile -t POINTS < <($HELPER make-exps "$GRID")
echo "${#POINTS[@]} grid points"

# Download the sequences first, so the calibration written below is not replaced by the download
read -r _ FIRST_EXP <<< "${POINTS[0]}"
pixi run get-resources "$FIRST_EXP"

trap '$HELPER restore "$GRID"' EXIT

for point in "${POINTS[@]}"; do
  read -r TAG EXP <<< "$point"
  echo -e "\n=== $TAG ==="
  $HELPER set-calib "$GRID" "$TAG"
  pixi run vslamlab "$EXP"
  pixi run evaluate "$EXP"
done

$HELPER summary "$GRID"
