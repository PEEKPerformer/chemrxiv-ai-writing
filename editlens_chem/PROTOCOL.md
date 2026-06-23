# EditLens-Chem — pre-registered protocol (second study)

A domain- and generation-adapted AI-edit-extent detector for chemistry full text,
built to test whether a purpose-trained model recovers the light-edit / newer-model
sensitivity that off-the-shelf EditLens leaves on the table. **This protocol is
frozen before any model is trained.** It is a *new* study; it does not modify the
parent study's `ANALYSIS_PLAN.md` or `DEVIATIONS.md`.

Status: design frozen 2026-06-23. Decisions below were made to maximize rigor and to
guarantee a publishable result under either outcome.

---

## 1. Question and claims (nested, so every outcome is informative)

- **Core (must-deliver, unimpeachable):** Does a chemistry+current-generation-adapted
  edit-extent regressor achieve higher **recall at a fixed 1% false-positive rate in
  the light-edit band** than EditLens, on **held-out generators, passages, and years**?
- **Headline (report only if the data support it):** *Detector aging.* Does detector
  sensitivity fall as generator capability rises, and does retraining on current
  generators recover it? (Requires the capability gradient + the commercial test set.)
- **Payoff (conditional on Core succeeding):** Re-measuring the corpus with the
  adapted detector, under identical pre-2022 p99 calibration, raises the 2026
  prevalence floor from 46% to a recovered estimate.

A null on the Core is a real result: it shows the in-domain edit signal is already
saturated by off-the-shelf detectors, which is the strongest defense of the parent
paper. The study is designed so we publish either way.

## 2. The decisions (made deliberately; rationale in §8)

| Decision | Choice |
|---|---|
| Target | Multi-task: (a) continuous edit-extent in [0,1] — human=0, polish/rewrite=measured edit_frac, **generate=1.0**; (b) auxiliary binary "AI-touched" head (presence), which is what matters at the light frontier. |
| Primary metric | **Recall @ 1% FPR**, FPR set on held-out pre-2022 human chemistry, reported **by edit-fraction band** (light 0–0.15 / moderate 0.15–0.5 / heavy >0.5), with passage-clustered bootstrap 95% CIs. |
| Splits | **Grouped by source passage** (all 7×3 variants + original of a passage in one fold) — non-negotiable anti-leakage. 5-fold grouped CV (Core) + **leave-one-generator-out** (cross-generator) + **held-out pre-2022 years** (temporal). Saved to disk with seed. |
| Architecture | Primary: **RoBERTa-large regressor** (mirror EditLens, isolates domain/generation effect from architecture). Secondary arm: a modern encoder (DeBERTa-v3-large or ModernBERT) — "can a stronger encoder crack the light band." Chunking matched to EditLens (~300 words). |
| Baselines (same held-out set) | EditLens RoBERTa + EditLens Llama (as-is); Pangram; Binoculars; a lexical excess-word classifier (the Gray/Siler proxy); **+ a domain-control ablation** (same architecture fine-tuned on non-chem edits) to separate *domain* gain from *generator-distribution* gain. |
| Calibration | pre-2022 p99 on the trained model's own outputs; corpus prevalence recomputed identically to the parent study. |
| Decision rule | Core "wins" iff light-band recall@1%FPR exceeds EditLens by a margin whose bootstrap 95% CI excludes 0 **on held-out generators**, AND the domain-control ablation shows the gain is not solely generator-distribution match. |

## 3. Data

- **Labeled edits (train+held-out):** the study's benchmark — 1,000 pre-2022 chemistry
  passages × 7 open generators × {polish, rewrite, generate} + originals (~21k variants,
  `results/raw/val_bench_variants.csv` + `validation/rewrites/<model>/<treatment>/<id>.txt`,
  cleaned of formatting contamination). edit_frac = 1 − SequenceMatcher ratio.
- **Human negative pool (FPR + calibration):** pre-2022 ChemRxiv chunks, drawn from the
  **latest pre-LLM window (2020–2022)** to minimize the human-style gap to deployment.
  These same pre-2022 human chunks also serve as negatives during training, so the
  training set and the calibration set overlap on the human side. The payoff
  re-measurement (S2) runs on 2022-onward papers the model never trained on, so the
  prevalence estimate is not circular, but this human-side overlap is stated here rather
  than left implicit.
- **Realistic-edit augmentation (construct validity, §4):** a held-in set of multi-turn
  / partial / realistic-prompt edits to make synthetic edits resemble real co-writing.
- **Real-anchor validation sets (test-only):** (i) within-paper **version pairs** across
  the ChatGPT boundary (genuine human revisions); (ii) **self-disclosed-AI papers** (the
  H7 set) as a small real positive set.
- **Commercial frontier test set (test-only, EXTERNAL DEPENDENCY):** a few hundred
  GPT-4o / Claude edits (polish/rewrite/generate, realistic prompts) of **held-out**
  pre-2022 passages. Never trained on. Requires grant funding + go-ahead.

## 4. Construct validity (the real ceiling — treated as first-class)

Training is single-shot synthetic; deployment is iterative human-AI co-writing. We
bound the gap rather than ignore it:
1. **Realistic edits:** add multi-turn (draft→AI→human→AI), partial (paragraph-level,
   not whole-passage), and journal-style-prompt edits to the training/eval mix.
2. **Real anchors:** validate the trained model on version-pairs and disclosed-AI
   papers; sensible behavior there bounds the synthetic→real leap.
3. **Commercial test set:** the only direct evidence that it generalizes to the models
   chemists actually use; everything else is extrapolation, and is labeled as such.

## 5. The period / style-drift confound (stated, partly irreducible)

Positives carry 2025-model style on pre-2022 content; negatives are pre-2022 human.
A fine-tuned model can learn "pre-2022 human register = human" and over-flag genuinely
human 2025 prose. Mitigations: latest-window negatives (2020–2022); a **domain-adversarial
year term** to strip period information from the representation; and a feature audit to
confirm the model is not keying on period markers. Residual risk is irreducible (no
clean known-human-2025 negative exists) and is disclosed.

## 6. Aging analysis (headline, if supported)

Our 7 generators span a capability gradient (llama-3.2-3b → qwen3-27b / glm-4.7 /
gpt-oss-20b). Report recall@1%FPR vs generator capability, by edit band, for EditLens
vs the adapted model. A falling EditLens curve that the adapted model flattens is the
aging effect, measured. The commercial set extends the gradient to the true frontier.

## 7. Integrity

- Splits, metric, and decision rule are frozen here **before training**.
- All evaluation is on held-out data; baselines run on the identical held-out set.
- A trained detector reopens the "you built it to find what you wanted" critique; the
  defenses are the frozen protocol, the off-the-shelf baselines, the domain-control
  ablation, and the real-anchor + commercial validation.
- Reproducibility: pinned base checkpoints (SHA), data hash, fixed seeds, splits saved
  to disk. HPC (UConn, A100s) per the parent study's node map.

## 8. Rationale for the harder choices

- *Why generate=1.0, not its edit_frac (~0.71):* generate is fully machine-authored
  regardless of its surface diff from a random original; edit_frac would mislabel it.
- *Why recall@1%FPR, not accuracy:* the parent study's credibility rests on a low FPR;
  a model that buys recall with false positives is worse, and accuracy hides this.
- *Why group-by-passage:* variant-level splitting leaks passage content and yields a
  memorization mirage.
- *Why the domain-control ablation:* "chem-trained beats EditLens" could merely be
  "any fine-tune matched to our 7 generators beats off-the-shelf"; the control earns
  the word "chemistry."
- *Why mirror EditLens architecture first:* isolates the effect of domain/generation
  adaptation from architecture before testing whether a stronger encoder helps.

## 9. Pipeline (this directory)

- `build_dataset.py` — assembles labeled examples + the grouped/LOGO/temporal splits,
  saved to disk (deterministic). Runnable on existing data now.
- `train.py` — RoBERTa-large multi-task regressor + presence head (HF Transformers),
  optional domain-adversarial year term. HPC.
- `baseline_editlens.py` — scores the identical held-out chunks with off-the-shelf
  EditLens (RoBERTa) so the head-to-head is on the same population. HPC.
- `evaluate.py` — recall@1%FPR by edit band, bootstrap CIs, baseline comparison,
  notation-density stratification (S10), aging curve, real-anchor + commercial-set
  evaluation. HPC.
- `stylometry.py` — the frozen S11 register-feature panel (feature definitions fixed
  here, before unblinding).
- `calibrate_and_apply.py` — pre-2022 p99 threshold + corpus prevalence recompute.

External dependency before the headline (aging/commercial) claim: the commercial
frontier test set (§3), pending grant + go-ahead.

## 10. Pre-specified secondary analysis: notation-density stratification

(Added 2026-06-23 after the training-pipeline smoke test, before any held-out
prediction was scored. The Zenodo release timestamps this section, with the rest of
the protocol, ahead of unblinding.)

Stratify the held-out recall@1%FPR advantage (EditLens-Chem minus off-the-shelf
EditLens) by the notation density of each held-out chunk: the fraction of tokens that
are chemistry surface markers (numerals, units, degree and Greek symbols, formula-like
tokens, NMR/MS data strings), split at the median into prose-heavy and notation-heavy
bins.

If the adaptation is chemical rather than a match to our seven generators (which the
S2 domain-control ablation already tests), the advantage should be larger in the
notation-heavy bin, where chemistry text departs most from the general text EditLens
was trained on. The operating point is the single global 1% FPR threshold; only the
recall numerator is split. This cut adds no data and no training, and does not change
the S2 decision rule. A flat or prose-concentrated result is reported as found.

## 11. Pre-specified stylometric feature audit (chemistry register)

(Added 2026-06-23 with Section 10, before any held-out prediction was scored.)

This operationalizes the S5 feature audit and gives an interpretable account of what AI
editing changes in chemistry prose. For each held-out chunk we compute a fixed panel of
register features, then compare human originals against each treatment (polish, rewrite,
generate), clustered by source passage, with Benjamini-Hochberg correction across the
panel.

Feature panel (rates per 1000 tokens unless noted):
- synthesis term-of-art verbs (afforded, furnished, yielded, obtained, subjected,
  quenched, eluted, recrystallized, refluxed, concentrated, stirred, isolated)
- copula rate (is, are, was, were)
- inflated abstract vocabulary (novel, crucial, pivotal, key, intricate, delve,
  elucidate, showcase, underscore, leverage)
- discourse connectives (moreover, furthermore, additionally, thus, hence)
- hedges (may, might, could, suggest, likely, presumably, possibly)
- notation density (the S10 metric)
- mean and variance of sentence length (burstiness)
- type-token ratio over a fixed 200-token window
- nominalization rate (tokens ending in -tion, -ment, -ance, -ity)
- punctuation rates, including em dashes per 1000 tokens

Primary question: which features separate human from AI-edited text at the light-edit
(polish) band, the frontier the detector targets. Secondary: whether the chemistry edit
signature differs from the general-text AI signature reported in prior work. This is
descriptive and does not change the S2 decision rule. The feature definitions are frozen
in `stylometry.py` in this release, so the audit is confirmatory, not exploratory.

Scope: this panel runs on the benchmark variants (human vs AI-edited). A corpus-wide
temporal version (features across 2017 to 2026 ChemRxiv) would belong to the parent
study and is not part of this protocol.
