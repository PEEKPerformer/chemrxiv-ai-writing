"""Score EditLens-Chem held-out chunks with off-the-shelf EditLens (roberta-large)
as the head-to-head baseline. Reuses train.py's split + chunking so the chunk
population is IDENTICAL to the trained model's heldout_pred_*.jsonl, applies
EditLens's required clean_text preprocessing, and emits its expected-bucket score
s in [0,1] -- mirroring code/score_editlens.py. Output schema matches train.py so
evaluate.py can compare the two directly.

  python baseline_editlens.py --mode cv --val-fold 0
  python baseline_editlens.py --mode logo --holdout-generator gptoss-20b
"""
import argparse
import contextlib
import json
import os
import re
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from train import build_chunk_examples, load_manifest, split_rows  # identical chunking

CHECKPOINT = "pangram/editlens_roberta-large"
BASE = "FacebookAI/roberta-large"
MAXLEN = 512

# ---- EditLens clean_text (vendored from code/score_editlens.py) -------------
BOILERPLATE_STARTS = ["Sure", "Here", "Abstract", "Title", "I'm happy to help", "Certainly"]


def _ws(t):
    return re.sub(r"\s+", " ", t).strip()


def _think(t):
    return t.split("</think>")[1].strip() if "</think>" in t else t


def _hdr(t):
    import emoji
    ps = [p for p in t.split("\n") if p.strip()]
    if not ps:
        return t
    first = emoji.replace_emoji(re.sub(r"^[^a-zA-Z0-9]*", "", ps[0]), "")
    if any(first.startswith(p) for p in BOILERPLATE_STARTS) and len(ps) > 1:
        t = "\n".join(ps[1:])
    return t


def clean_text(t):
    import emoji
    return _ws(_hdr(_think(emoji.demojize(t))).lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest.jsonl"))
    ap.add_argument("--splits", default=os.path.join(HERE, "splits.json"))
    ap.add_argument("--mode", choices=["cv", "logo"], default="cv")
    ap.add_argument("--val-fold", type=int, default=0)
    ap.add_argument("--holdout-generator", default=None)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    a = ap.parse_args()

    rows = load_manifest(a.manifest)
    splits = json.load(open(a.splits))
    _, ho_rows = split_rows(rows, a.mode, a.val_fold, a.holdout_generator, splits)
    tag = a.mode + (f"_fold{a.val_fold}" if a.mode == "cv" else f"_holdout-{a.holdout_generator}")
    ho = build_chunk_examples(ho_rows)
    print(f"[{tag}] heldout chunks={len(ho)}", flush=True)

    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(BASE)
    model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT).to(dev).eval()
    n_buckets = model.config.num_labels
    weights = np.arange(n_buckets)
    autocast = (torch.autocast("cuda", dtype=torch.bfloat16) if dev == "cuda"
                else contextlib.nullcontext())

    texts = [clean_text(r["text"]) for r in ho]
    order = sorted(range(len(texts)), key=lambda k: len(texts[k]))  # length-batched throughput
    scores = [None] * len(texts)
    with torch.no_grad():
        for b0 in range(0, len(order), a.batch_size):
            idxs = order[b0:b0 + a.batch_size]
            enc = tok([texts[k] for k in idxs], truncation=True, max_length=MAXLEN,
                      padding=True, return_tensors="pt").to(dev)
            with autocast:
                logits = model(**enc).logits.float()
            p = torch.softmax(logits, dim=-1).cpu().numpy()
            for j, k in enumerate(idxs):
                scores[k] = float(p[j] @ weights) / (n_buckets - 1)

    os.makedirs(a.out, exist_ok=True)
    outp = os.path.join(a.out, f"editlens_pred_{tag}.jsonl")
    with open(outp, "w") as f:
        for r, s in zip(ho, scores):
            f.write(json.dumps({"passage": r["passage"], "model": r["model"], "year": r["year"],
                                "extent": r["extent"], "presence": r["presence"],
                                "pred_extent": s}) + "\n")
    print(f"wrote {outp} (n_buckets={n_buckets})", flush=True)


if __name__ == "__main__":
    main()
