"""EditLens-Chem evaluation: recall @ fixed FPR, by edit band, passage-clustered
bootstrap CIs, and head-to-head vs baselines (PROTOCOL.md S2). Pure-numpy metric core.

Inputs are prediction JSONL files (one row per held-out chunk or paper):
  {passage, extent, presence, pred_extent, [model]}
- The FPR threshold is set on presence==0 (held-out human) rows.
- Recall is computed on presence==1 rows, binned by ground-truth `extent` into
  light (0,0.15] / moderate (0.15,0.5] / heavy (>0.5).
Pass --baseline to compare a second predictions file (e.g., EditLens on the SAME
held-out chunks); the script reports the per-band recall delta with a bootstrap CI.

  python editlens_chem/evaluate.py --pred runs/heldout_pred_logo_holdout-gptoss-20b.jsonl \
         --baseline runs/editlens_pred_logo_holdout-gptoss-20b.jsonl --fpr 0.01
  python editlens_chem/evaluate.py --selftest
"""
import argparse
import json
import os
import re
import sys

import numpy as np

BANDS = [("light(0-.15]", 0.0, 0.15), ("moderate(.15-.5]", 0.15, 0.5), ("heavy(>.5]", 0.5, 1.01)]

# ---- notation density: fraction of tokens that are chemistry surface markers ----
# (numerals, units, Greek/special symbols, formula-like tokens) -- see PROTOCOL.md S10
UNIT_RE = re.compile(
    r"^(?:m?L|m?mol|mol|[muμnk]?M|[muμn]?g|K|nm|Hz|[MGk]?Hz|ppm|equiv|"
    r"mol%|wt%|v/v|h|min|kJ|eV|mmHg|rpm|Å)$", re.I)
GREEK_SPECIAL = set("αβγδεζηθκλμ"
                    "νξπρστφχψω"
                    "°±×·→⇌≈≤≥ΔΩ")
FORMULA_RE = re.compile(r"[A-Z][a-z]?\d|[A-Z][a-z]?[A-Z]")  # CDCl3, H2O, CH2, NaH, etc.


def notation_density(text):
    toks = text.split()
    if not toks:
        return 0.0
    n = 0
    for t in toks:
        s = t.strip(".,;:()[]{}")
        if (any(c.isdigit() for c in s) or UNIT_RE.match(s)
                or any(c in GREEK_SPECIAL for c in t) or FORMULA_RE.search(s)):
            n += 1
    return n / len(toks)


def heldout_densities(manifest, splits_path, mode, val_fold, holdout_generator):
    """Recompute, in train.py's deterministic chunk order, the notation density of
    each held-out chunk -- so it aligns index-for-index with the prediction files
    (both were written by zipping over build_chunk_examples(ho_rows))."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from train import build_chunk_examples, load_manifest, split_rows
    rows = load_manifest(manifest)
    sp = json.load(open(splits_path))
    _, ho_rows = split_rows(rows, mode, val_fold, holdout_generator, sp)
    chunks = build_chunk_examples(ho_rows)
    return chunks, [notation_density(c["text"]) for c in chunks]


def load(path):
    return [json.loads(l) for l in open(path)]


def threshold_at_fpr(rows, fpr):
    """tau such that exactly `fpr` of human (presence==0) rows score above it."""
    neg = np.array([r["pred_extent"] for r in rows if r["presence"] == 0])
    if len(neg) == 0:
        raise ValueError("no presence==0 (human) rows to set the FPR threshold")
    return float(np.quantile(neg, 1.0 - fpr)), len(neg)


def recall_by_band(rows, tau):
    out = {}
    for name, lo, hi in BANDS:
        pos = [r for r in rows if r["presence"] == 1 and lo < r["extent"] <= hi]
        out[name] = (np.mean([r["pred_extent"] > tau for r in pos]) if pos else float("nan"),
                     len(pos))
    return out


def boot_recall(rows, fpr, n=2000, seed=20260623):
    """passage-clustered bootstrap of recall@fpr per band -> 95% CIs."""
    rng = np.random.default_rng(seed)
    by_p = {}
    for r in rows:
        by_p.setdefault(r["passage"], []).append(r)
    passages = list(by_p)
    acc = {name: [] for name, _, _ in BANDS}
    for _ in range(n):
        samp = [x for p in rng.choice(passages, len(passages), replace=True) for x in by_p[p]]
        try:
            tau, _ = threshold_at_fpr(samp, fpr)
        except ValueError:
            continue
        rb = recall_by_band(samp, tau)
        for name in acc:
            if not np.isnan(rb[name][0]):
                acc[name].append(rb[name][0])
    return {name: (np.nanpercentile(v, 2.5), np.nanpercentile(v, 97.5)) if v else (np.nan, np.nan)
            for name, v in acc.items()}


def report(rows, fpr, label):
    tau, nneg = threshold_at_fpr(rows, fpr)
    rb = recall_by_band(rows, tau)
    ci = boot_recall(rows, fpr)
    print(f"\n[{label}] tau@{fpr:.0%}FPR={tau:.3f} (human n={nneg})")
    for name, _, _ in BANDS:
        r, npos = rb[name]
        lo, hi = ci[name]
        print(f"  recall {name:16s}: {r:.3f} [{lo:.3f}, {hi:.3f}]  (n={npos})")
    return rb


def align_densities(rows, chunks, densities):
    """attach density to each prediction row by index; assert the alignment holds."""
    if len(rows) != len(chunks):
        raise SystemExit(f"alignment: {len(rows)} pred rows vs {len(chunks)} chunks")
    for r, c in zip(rows, chunks):
        if r["passage"] != c["passage"] or abs(r["extent"] - c["extent"]) > 1e-9:
            raise SystemExit("alignment: pred row does not match reconstructed chunk "
                             f"({r['passage']}/{r['extent']} vs {c['passage']}/{c['extent']})")
    return [(r, d) for r, d in zip(rows, densities)]


def recall_by_density(rows, densities, tau, thr):
    """recall at a FIXED global tau, split into prose-heavy vs notation-heavy chunks."""
    out = {}
    for name, lo, hi in [("prose(<=med)", -1.0, thr), ("notation(>med)", thr, 2.0)]:
        pos = [r for r, d in zip(rows, densities)
               if r["presence"] == 1 and lo < d <= hi]
        out[name] = (np.mean([r["pred_extent"] > tau for r in pos]) if pos else float("nan"),
                     len(pos))
    return out


def report_density(rows, densities, fpr, label, thr):
    tau, nneg = threshold_at_fpr(rows, fpr)
    rd = recall_by_density(rows, densities, tau, thr)
    print(f"\n[{label}] tau@{fpr:.0%}FPR={tau:.3f} (human n={nneg}); "
          f"density median={thr:.3f}")
    for name in ("prose(<=med)", "notation(>med)"):
        r, npos = rd[name]
        print(f"  recall {name:16s}: {r:.3f}  (n={npos})")
    return rd


def selftest():
    rng = np.random.default_rng(0)
    rows = []
    for p in range(200):
        rows.append({"passage": p, "presence": 0, "extent": 0.0,
                     "pred_extent": float(rng.beta(2, 8))})            # humans: low scores
        for ext in (0.08, 0.3, 0.8):                                   # light/mod/heavy
            base = {0.08: 3, 0.3: 5, 0.8: 9}[ext]                      # heavier -> higher score
            rows.append({"passage": p, "presence": 1, "extent": ext,
                         "pred_extent": float(rng.beta(base, 4))})
    report(rows, 0.01, "selftest")
    print("\nselftest OK: recall should rise light < moderate < heavy.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred")
    ap.add_argument("--baseline")
    ap.add_argument("--fpr", type=float, default=0.01)
    ap.add_argument("--selftest", action="store_true")
    # notation-density stratification (PROTOCOL.md S10); needs the source chunks
    ap.add_argument("--density-manifest")
    ap.add_argument("--density-splits")
    ap.add_argument("--mode", choices=["cv", "logo"], default="cv")
    ap.add_argument("--val-fold", type=int, default=0)
    ap.add_argument("--holdout-generator", default=None)
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    pred_rows = load(a.pred)
    model_rb = report(pred_rows, a.fpr, "EditLens-Chem")
    base_rows = load(a.baseline) if a.baseline else None
    if base_rows is not None:
        base_rb = report(base_rows, a.fpr, "baseline")
        print("\nDELTA (chem - baseline), recall@%.0f%%FPR by band:" % (a.fpr * 100))
        for name, _, _ in BANDS:
            d = model_rb[name][0] - base_rb[name][0]
            print(f"  {name:16s}: {d:+.3f}")
        print("\nCore decision: chem wins iff light-band delta CI excludes 0 on held-out "
              "generators AND the domain-control ablation shows the gain is not generator-match.")

    if a.density_manifest:
        chunks, densities = heldout_densities(
            a.density_manifest, a.density_splits or a.density_manifest.replace(
                "manifest.jsonl", "splits.json"),
            a.mode, a.val_fold, a.holdout_generator)
        thr = float(np.median(densities))
        align_densities(pred_rows, chunks, densities)            # index-alignment guard
        print("\n=== notation-density stratification (PROTOCOL.md S10) ===")
        m_rd = report_density(pred_rows, densities, a.fpr, "EditLens-Chem", thr)
        if base_rows is not None:
            align_densities(base_rows, chunks, densities)
            b_rd = report_density(base_rows, densities, a.fpr, "baseline", thr)
            print("\nDELTA (chem - baseline), recall@%.0f%%FPR by density bin:" % (a.fpr * 100))
            for name in ("prose(<=med)", "notation(>med)"):
                print(f"  {name:16s}: {m_rd[name][0] - b_rd[name][0]:+.3f}")
            print("\nPre-specified prediction: the advantage concentrates in notation(>med).")


if __name__ == "__main__":
    main()
