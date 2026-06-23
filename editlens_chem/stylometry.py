"""EditLens-Chem stylometric feature audit (PROTOCOL.md S11). The feature panel below
is the pre-registered one, frozen before unblinding. It computes register features per
benchmark variant, then compares human originals against each treatment (polish,
rewrite, generate), paired and clustered by source passage, with Benjamini-Hochberg
correction across the panel. The audit is on text only; it does not use the detector.

  python stylometry.py --manifest manifest.jsonl
  python stylometry.py --selftest
"""
import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from evaluate import notation_density  # the S10 metric, single shared definition

WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
SENT = re.compile(r"[.!?]+(?:\s|$)")

TERM_VERBS = {"afforded", "furnished", "yielded", "obtained", "subjected", "quenched",
              "eluted", "recrystallized", "refluxed", "concentrated", "stirred", "isolated"}
COPULA = {"is", "are", "was", "were"}
INFLATED = {"novel", "crucial", "pivotal", "key", "intricate", "delve", "elucidate",
            "showcase", "underscore", "leverage"}
CONNECTIVES = {"moreover", "furthermore", "additionally", "thus", "hence"}
HEDGES = {"may", "might", "could", "suggest", "likely", "presumably", "possibly"}
NOMINAL = ("tion", "ment", "ance", "ity")

PANEL = ["term_verbs", "copula", "inflated", "connectives", "hedges", "notation_density",
         "sent_len_mean", "sent_len_var", "ttr_200", "nominalization", "em_dash"]


def _words(text):
    return [w.lower() for w in WORD.findall(text)]


def features(text):
    """The frozen S11 panel. Set-membership rates are per 1000 word-tokens."""
    w = _words(text)
    n = len(w) or 1
    k = 1000.0 / n

    def rate(s):
        return k * sum(1 for x in w if x in s)

    sents = [s for s in SENT.split(text) if s.strip()]
    slens = [len(_words(s)) for s in sents] or [n]
    ttr = len(set(w[:200])) / min(200, n)
    return {
        "term_verbs": rate(TERM_VERBS),
        "copula": rate(COPULA),
        "inflated": rate(INFLATED),
        "connectives": rate(CONNECTIVES),
        "hedges": rate(HEDGES),
        "notation_density": notation_density(text),
        "sent_len_mean": float(np.mean(slens)),
        "sent_len_var": float(np.var(slens)),
        "ttr_200": ttr,
        "nominalization": k * sum(1 for x in w if x.endswith(NOMINAL)),
        "em_dash": 1000.0 * text.count("—") / n,
    }


def passage_paired_diffs(rows, treatment):
    """per-passage paired difference (treatment minus human original) for each feature.
    Multiple generator variants of a treatment in a passage are averaged first, so each
    passage contributes one value per feature (the clustering unit)."""
    by_p = {}
    for r in rows:
        by_p.setdefault(r["id"], {}).setdefault(r["treatment"], []).append(r["_feat"])
    diffs = {f: [] for f in PANEL}
    for td in by_p.values():
        if "original" not in td or treatment not in td:
            continue
        h = td["original"][0]
        for f in PANEL:
            tv = float(np.mean([x[f] for x in td[treatment]]))
            diffs[f].append(tv - h[f])
    return diffs


def boot(d, n=2000, seed=20260623):
    d = np.asarray(d, float)
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(d, len(d), replace=True).mean() for _ in range(n)])
    p = 2.0 * min((means > 0).mean(), (means < 0).mean())
    return (float(d.mean()), float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)), float(min(1.0, p)))


def bh(pvals):
    """Benjamini-Hochberg adjusted p-values."""
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        idx = order[rank]
        prev = min(prev, p[idx] * m / (rank + 1))
        adj[idx] = prev
    return adj


def report(rows):
    for r in rows:
        r["_feat"] = features(r["text"])
    for treatment in ("polish", "rewrite", "generate"):
        diffs = passage_paired_diffs(rows, treatment)
        if not any(diffs[f] for f in PANEL):
            print(f"\n[{treatment}] no paired passages found")
            continue
        stats = {f: boot(diffs[f]) for f in PANEL}
        adj = bh([stats[f][3] for f in PANEL])
        npass = len(diffs[PANEL[0]])
        print(f"\n[{treatment} - human] paired by passage (n={npass}); "
              "diff [95% CI], BH-adjusted p")
        for f, q in zip(PANEL, adj):
            mean, lo, hi, _ = stats[f]
            star = "*" if q < 0.05 else " "
            print(f"  {star} {f:18s}: {mean:+8.3f} [{lo:+7.3f}, {hi:+7.3f}]  q={q:.3f}")


def selftest():
    rng = np.random.default_rng(0)
    base = ("To a stirred solution of the substrate (1.0 g, 5.2 mmol) in THF (20 mL) at "
            "0 C was added the reagent. The mixture was refluxed for 2 h and afforded the "
            "product (85%). 1H NMR (400 MHz, CDCl3): d 7.26 (d, J = 8.0 Hz, 2H).")
    ai = ("This novel and crucial transformation showcases a pivotal advance. Moreover, "
          "the reaction is significant. Furthermore, it could potentially be useful and "
          "may suggest broad applicability across the intricate landscape of synthesis.")
    rows = []
    for p in range(40):
        rows.append({"id": f"p{p}", "treatment": "original", "text": base})
        rows.append({"id": f"p{p}", "treatment": "polish", "text": base + " " + ai})
    report(rows)
    print("\nselftest OK: inflated/connectives/hedges should rise, term_verbs/notation fall.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest.jsonl"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    rows = [json.loads(l) for l in open(a.manifest)]
    report(rows)


if __name__ == "__main__":
    main()
