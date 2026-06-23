#!/bin/bash
# usage: sbatch train.sbatch cv 0      (mode=cv, val-fold=0)
#        sbatch train.sbatch logo gptoss-20b
#SBATCH --job-name=elchem_train
#SBATCH --partition=general-gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/ada08003/brf22001/chemrxiv-pangram/editlens_chem/train_%x_%j.out

set -euo pipefail
MODE=${1:?mode: cv|logo}
ARG=${2:?fold number or generator name}
ROOT=/scratch/ada08003/brf22001/chemrxiv-pangram
cd "$ROOT/editlens_chem"

source "$ROOT/venv/bin/activate"
export HF_HOME="$ROOT/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

echo "=== node $(hostname) | mode=$MODE arg=$ARG ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1 || true

if [ "$MODE" = "cv" ]; then
  python train.py --mode cv --val-fold "$ARG" --epochs 3 \
    --base FacebookAI/roberta-large --out "$ROOT/editlens_chem/runs"
else
  python train.py --mode logo --holdout-generator "$ARG" --epochs 3 \
    --base FacebookAI/roberta-large --out "$ROOT/editlens_chem/runs"
fi
echo "=== DONE ==="
