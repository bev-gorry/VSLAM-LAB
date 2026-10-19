#!/bin/bash
# Unattended run: the VPR matrix of the joint Sesoko sequence, then the two camera verification grids (2018 first,
# the shorter one). Waits for a VPR extraction that is already running instead of starting a second one; VPR skips
# sskall-full if its D.npy already exists. Everything is logged to calib_grid/logs/.
#
# Usage (from the VSLAM-LAB root):  bash calib_grid/run_vpr_and_verify.sh
set -euo pipefail

mkdir -p calib_grid/logs
LOG=calib_grid/logs/vpr_and_verify_$(date +%Y%m%d_%H%M).log
exec > >(tee -a "$LOG") 2>&1

while pgrep -f "vpr-lab.py" > /dev/null; do
  echo "$(date +%H:%M) waiting for the running VPR extraction to finish ..."
  sleep 300
done

echo "=== $(date +%H:%M) VPR matrix: sesoko sskall-full"
pixi run vpr sesoko sskall-full

for grid in calib_grid/grid_sesoko_full_18_verify.yaml calib_grid/grid_sesoko_full_1617_verify.yaml; do
  echo "=== $(date +%H:%M) verification: $grid"
  bash calib_grid/run_calib_grid.sh "$grid"
done
echo "=== $(date +%H:%M) done; summaries in VSLAM-LAB-Evaluation/calib_grid_sesoko_full_*_verify_summary.csv"
