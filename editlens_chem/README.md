# EditLens-Chem (second study)

A domain- and generation-adapted AI-edit-extent detector for chemistry, built to test
whether a purpose-trained model recovers the light-edit / newer-model sensitivity that
off-the-shelf EditLens misses. Design is **frozen** in `PROTOCOL.md` (read it first).

This is a *separate* study. It does **not** modify the parent study's `ANALYSIS_PLAN.md`
or `DEVIATIONS.md`.

## Run order
1. `python editlens_chem/build_dataset.py` — labeled examples + frozen splits
   (group-by-passage CV, leave-one-generator-out, temporal). *Runnable now; tested.*
   Writes `manifest.jsonl` (gitignored, ~50 MB, reproducible) + `splits.json`.
2. `python editlens_chem/train.py --mode {cv|logo} ...` — multi-task RoBERTa-large
   (extent regression + AI-touched presence), optional adversarial-year term. **HPC/GPU.**
3. `python editlens_chem/evaluate.py --pred ... --baseline ...` — recall @ 1% FPR by
   edit band, passage-bootstrap CIs, head-to-head vs EditLens/Pangram/Binoculars/lexical.
   Metric core is tested (`--selftest`). Baselines must be scored on the *same* held-out chunks.
4. `calibrate_and_apply` (to write) — pre-2022 p99 threshold on the trained model, then
   recompute corpus prevalence identically to the parent study (the "payoff" claim).

## Status
- ✅ Protocol frozen; dataset + splits built and verified (21,967 variants, 1,000 passages,
  6,794 light-edit examples; 5 grouped folds, 7 LOGO generators).
- ✅ Evaluation metric (recall@1%FPR by band + bootstrap) implemented and self-tested.
- ⏳ `train.py` / `evaluate.py` baseline-scoring: HPC-ready scaffolds, **not yet run** (GPU).
- ⛔ `calibrate_and_apply` + the **commercial-model test set** (GPT-4o/Claude, test-only)
  are pending — the commercial set needs grant funding + go-ahead and is the load-bearing
  evidence for the detector-aging / commercial-generalization claim.

## The one external dependency
LOGO tests generalization across *open* models; the corpus is commercial. A few-hundred-
example commercial test set (held-out passages, realistic prompts, never trained on) is
what converts "generalizes among open models" into "detects what chemists actually use."
