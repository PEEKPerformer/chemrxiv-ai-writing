#!/bin/bash
#SBATCH --job-name=elchem_smoke
#SBATCH --partition=general-gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/ada08003/brf22001/chemrxiv-pangram/editlens_chem/smoke_%j.out

set -euo pipefail
ROOT=/scratch/ada08003/brf22001/chemrxiv-pangram
cd "$ROOT/editlens_chem"

source "$ROOT/venv/bin/activate"
export HF_HOME="$ROOT/hf_cache"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

echo "=== node $(hostname) ==="
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
python -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-')"

# tiny end-to-end: 1 CV fold, 1 epoch, capped rows -> validates load->chunk->train->predict->write
python train.py --mode cv --val-fold 0 --epochs 1 --limit 500 \
  --base FacebookAI/roberta-large --out "$ROOT/editlens_chem/runs_smoke"

echo "=== smoke output ==="
ls -la "$ROOT/editlens_chem/runs_smoke"
head -2 "$ROOT/editlens_chem/runs_smoke/heldout_pred_cv_fold0.jsonl"
echo "=== DONE ==="
