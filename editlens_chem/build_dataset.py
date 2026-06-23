"""EditLens-Chem dataset + frozen splits (per PROTOCOL.md). Runnable on existing data.

Assembles one example per benchmark variant (original + 7 generators x 3 treatments)
with the protocol target, then writes deterministic splits to disk:
  - grouped 5-fold by SOURCE PASSAGE id (anti-leakage; all variants of a passage in one fold)
  - leave-one-generator-out (7 folds)
  - held-out pre-2022 YEAR (temporal generalization)
Target: extent in [0,1] = 0 (original/human) | edit_frac (polish, rewrite) | 1.0 (generate);
        presence = 0 (original) else 1.
train.py consumes manifest.jsonl + splits.json and chunks internally (~300 words, EditLens-matched).

  python editlens_chem/build_dataset.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

SEED = 20260623
RAW = os.path.join(config.RESULTS_DIR, "raw")
RW = os.path.join(config.SCRAPER_DIR, "validation", "rewrites")
PASSAGES = os.path.join(config.SCRAPER_DIR, "validation", "passages.jsonl")
OUT = os.path.dirname(os.path.abspath(__file__))


def load_original_texts():
    txt = {}
    if os.path.exists(PASSAGES):
        for line in open(PASSAGES):
            d = json.loads(line)
            txt[d["id"]] = d.get("t", "")
    return txt


def target(treatment, edit_frac):
    if treatment == "original":
        return 0.0, 0
    if treatment == "generate":
        return 1.0, 1                      # fully machine-authored regardless of surface diff
    return float(edit_frac), 1             # polish / rewrite -> measured edit extent


def main():
    v = pd.read_csv(os.path.join(RAW, "val_bench_variants.csv"))
    orig = load_original_texts()
    rows = []
    miss = 0
    for r in v.itertuples():
        if r.model == "original":
            text = orig.get(r.id, "")
        else:
            fp = os.path.join(RW, r.model, r.treatment, f"{r.id}.txt")
            text = open(fp).read().strip() if os.path.exists(fp) else ""
        if len(text.split()) < 50:
            miss += 1
            continue
        ext, pres = target(r.treatment, r.edit_frac)
        rows.append({"id": r.id, "model": r.model, "treatment": r.treatment,
                     "sec": r.sec, "year": int(r.y), "edit_frac": float(r.edit_frac),
                     "extent": ext, "presence": pres, "n_words": len(text.split()),
                     "text": text})
    df = pd.DataFrame(rows)
    print(f"examples: {len(df)} (skipped {miss} <50 words) | passages: {df.id.nunique()} | "
          f"generators: {sorted(df.model.unique())}")
    print("by treatment:\n", df.treatment.value_counts().to_string())
    band = pd.cut(df.extent, [-0.01, 0.0, 0.15, 0.5, 1.01],
                  labels=["human(0)", "light(0-.15)", "moderate(.15-.5)", "heavy(>.5)"])
    print("by edit band:\n", band.value_counts().to_string())

    rng = np.random.default_rng(SEED)
    passages = sorted(df.id.unique())
    rng.shuffle(passages)
    fold_of = {p: i % 5 for i, p in enumerate(passages)}   # grouped 5-fold by passage
    df["cv_fold"] = df.id.map(fold_of)

    # leave-one-generator-out: test fold = that generator's NON-original variants
    gens = sorted(m for m in df.model.unique() if m != "original")
    logo = {g: {"test_generator": g} for g in gens}

    # temporal: held-out source years = the latest pre-2022 years present
    years = sorted(int(y) for y in df.year.unique())
    holdout_years = years[-2:] if len(years) >= 4 else years[-1:]
    df["temporal_split"] = np.where(df.year.isin(holdout_years), "test", "train")

    df.to_json(os.path.join(OUT, "manifest.jsonl"), orient="records", lines=True)
    splits = {"seed": SEED, "scheme": "grouped-by-passage",
              "cv_folds": 5, "logo_generators": gens,
              "temporal_holdout_years": holdout_years,
              "fold_sizes": {int(k): int(v) for k, v in
                             df.cv_fold.value_counts().sort_index().to_dict().items()},
              "n_examples": int(len(df)), "n_passages": int(df.id.nunique())}
    json.dump(splits, open(os.path.join(OUT, "splits.json"), "w"), indent=1)
    print(f"\ngrouped 5-fold sizes: {splits['fold_sizes']}")
    print(f"LOGO generators: {gens}")
    print(f"temporal holdout years: {holdout_years} "
          f"(test n={int((df.temporal_split=='test').sum())})")
    print(f"wrote manifest.jsonl ({len(df)} rows) + splits.json")


if __name__ == "__main__":
    main()
