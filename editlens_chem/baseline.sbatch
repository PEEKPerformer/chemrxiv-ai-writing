#!/bin/bash
# usage: sbatch baseline.sbatch cv 0   |   sbatch baseline.sbatch logo gptoss-20b
#SBATCH --job-name=elchem_base
#SBATCH --partition=general-gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/ada08003/brf22001/chemrxiv-pangram/editlens_chem/base_%x_%j.out

set -euo pipefail
MODE=${1:?mode: cv|logo}
ARG=${2:?fold number or generator name}
ROOT=/scratch/ada08003/brf22001/chemrxiv-pangram
cd "$ROOT/editlens_chem"

source "$ROOT/venv/bin/activate"
export HF_HOME="$ROOT/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

echo "=== node $(hostname) | EditLens baseline mode=$MODE arg=$ARG ==="
if [ "$MODE" = "cv" ]; then
  python baseline_editlens.py --mode cv --val-fold "$ARG" --out "$ROOT/editlens_chem/runs"
else
  python baseline_editlens.py --mode logo --holdout-generator "$ARG" --out "$ROOT/editlens_chem/runs"
fi
echo "=== DONE ==="
