# Deviations & results log (append-only)

The registration is frozen at the GitHub releases `v1.0.0-plan` /
`v1.1.0-plan` / `v1.2.0-plan` and their **immutable Zenodo deposits** — those
are the authoritative registration anchor and were never altered. The working
`ANALYSIS_PLAN.md` is now held byte-identical to `v1.2.0-plan`. Disclosure
(audit PREREG-01): during 2026-06-12…16 the working `ANALYSIS_PLAN.md` was
edited in place with interim results across several commits, then on 2026-06-16
(commit `cf66b33`) restored byte-identical to the frozen tag, with all results
migrated into this file. No registered prediction was ever rewritten, and the
tag/Zenodo anchor is intact, so this is not post-hoc hypothesizing — but the
plan was not continuously immutable in the working tree. This file is intended
as an **append-only** record going forward (git history of this file is the
audit trail); the meta header is corrected for accuracy where needed, entries
are not. Entry dates are analysis dates (analyses ran 2026-06-10 through
2026-06-16); the git commit dates of this file are authoritative.

Format per entry: hypothesis — registered → actual → reason.

---

## H1 (validation benchmark, §4.1) — PASS
Registered: Spearman(score, edit_frac) > 0, p < 0.05, passage-clustered.
Result: rho = 0.812 (passage-clustered bootstrap 95% 0.803–0.821). PASS.
Specificity: 28/1000 originals flagged (2.8% at passage level; paper-level
FPR = 1% by threshold construction — passages have higher score variance
than 19-chunk papers).

## H1a (generator transfer, §4.1) — HOLDS
Registered: 2026-trio generate-sensitivity within 10 pp below the 2024
control. Result: trio 97.0% vs control (Qwen2.5-7B) 98.1%, diff −1.1 pp.
HOLDS.

### Deviation (§4.1) — generation contamination corrected
A QC audit found generation-time extraction failures: gemma4-12b special
tokens (`<turn|>`/`<pad>`) and a reasoning channel; llama32-3b polish
preamble; gpt-oss rewrite markdown. Outputs were normalized
(src/clean_rewrites.py; raw backed up to validation/rewrites_raw/) and the
benchmark re-scored. Effect on conclusions: none (gemma4 generate
93.7→94.8%, gpt-oss rewrite 74.7→69.9%; H1/H1a unchanged).

### Deviation (cross-cutting) — bootstrap p-values
The originally-coded p = mean(boots ≤ null) is not a valid test statistic.
Replaced with a null-centered bootstrap ASL (H1, H4) and a two-sample
bootstrap (H2). Percentile CIs are the primary inference. Directions
unchanged.

## H2 (mixture prevalence, §4.2) — PASS; consistency check failed
Registered: π_2025 > π_2022 (p < 0.05); consistency check π ≥ flag rate.
Result: π_2025 8.0% vs π_2022 0.2% (generate F_AI), two-sample bootstrap
p < 0.0001. PASS.
Deviation: the consistency check does not hold — π < flag rate every year.
Reason: F_AI is predominantly-AI text, so π estimates predominant-AI
prevalence, while the flag rate counts any threshold crossing. Reported as a
bracket: predominant-AI 14.5% / substantial 32% / any-detectable 46% (2026).
A continuous-dose mixture (the proper resolution) is not implemented.

## H3 (changepoint, §4.3) — FAIL
Registered: breakpoint 95% CI contains 2022-12.
Result: breakpoint MLE 2022-01, CI 2021-09…2022-06; excludes 2022-12. FAIL.
Reason: a single broken line cannot fit a convex multi-year rise and places
the kink early. Model not changed. Exploratory (non-registered) onset
measure — first 3-consecutive-month run above the pre-2022 floor upper-95%
bound — is 2023-06.

## H4 (author panel, §4.4) — PASS
Registered: P(next flagged | current flagged) > P(next flagged | current
not), MH within posting year, author-clustered bootstrap.
Result: 45.2% vs 13.9%; MH OR = 3.61 [3.18–4.09], null-centered bootstrap
p ≈ 0. PASS. Limitation: papers attributed to all co-authors, so persistence
is a paper-sequence property, not isolated to one author.

## H5 (homogenization, §4.5) — FAIL (null)
Registered: Spearman(year, dispersion) < 0, p < 0.05.
Result: dispersion 0.092/0.089/0.092/0.092/0.101 (2022–26); Spearman = +0.40
(wrong sign), bootstrap p = 0.95. FAIL. n = 5 yearly points; top-200-word
profile only.

## H6 (reference verification, §4.6) — UNTESTED
Registered: flagged > unflagged unverifiable-reference rate, MH within year,
incl. a non-DOI Crossref bibliographic-query channel.
Result: DOI-existence channel run (src/parse_references.py); inconclusive —
pre-2022 unverifiable-DOI rate 24% is PDF-extraction noise, not fabrication,
which sends the calibration cutoff to 100% (MH undefined). Raw means:
flagged 22.7% vs unflagged 16.0% (noise-dominated, confounded).
Deviation: the registered non-DOI bibliographic-query channel is not
implemented; it is required to test H6. H6 is untested, not null.

## H7 (disclosure gap, §4.8) — registered prediction holds (<25%)
Registered: < 25% of flagged 2024–2026 papers carry an AI-use disclosure.
Result: 166/5,235 = 3.17% (Wilson 2.73–3.68); unflagged 0.85%; pre-2022
calibration 0.00%; sample precision ~92%. < 25% holds.
Matcher refined over three passes (each changed the estimate):
1. Negative declarations split to their own tier (bug): 2.27% → 2.25%.
2. Sample-validation false positives ("curie"→Curie-Weiss; "claude"→Univ.
   Claude Bernard; AI-term+writing-word matching citations/titles) →
   required a disclosure frame: 2.25% → 1.60%.
3. Recall audit (frame-only missed passive voice and non-acknowledgment
   sections) → final matcher = AI-term AND use-frame (incl. passive) AND
   writing-object, over {acknowledgments, competing, author_info,
   conclusion, other, data_avail}, with a negative-boilerplate guard:
   1.60% → 3.17%.
Superseded values: 1.60% (under-recall), 3.84% (under-precision interim).

## H6 (reference verification, §4.6) — channel B result: NULL (2026-06-17)
Channel B (Crossref query.bibliographic) implemented and run after channel A
was inconclusive. Matcher segments reference tails, fuzzy-matches each ref,
classifies verifiable/unverifiable; validated by 4 independent agents on 125
refs (precision/recall + failure modes), then hardened (embedded/PII/Nature-URL
DOI extraction, component-DOI filter, NFKD+edit-distance author match,
contextual year, structural-source bucket, parent-DOI exclusion).
Result (n=350 post-2022 papers, 60/cell): per-paper unverifiable rate
flagged 2.9% vs unflagged 2.8%; per-ref flagged 4.7% vs unflagged 5.7% vs
pre-2022 6.1%. MH OR = 1.04 [0.18-4.97], bootstrap p=0.99. NO difference
between flagged and unflagged papers.
Caveats: matcher false-negative floor ~6% on real refs (not the registered
<=1% calibration target — legitimately-hard citations: pre-DOI/conference/
books/title-free), so the absolute rate is not a fabrication rate; only the
cross-group comparison is interpreted. Underpowered for rare fabrications
(wide CI). Validation found genuine fabricated references (3/125, all in
flagged papers, DOI-404 + zero title match) — real but too rare to produce a
paper-level differential. Conclusion: no evidence flagged papers carry more
unverifiable references; isolated fabrications occur but are rare.

## Audit remediation — full study audit (2026-06-17)

A second, more exhaustive multi-agent audit (8 dimensions, adversarial
refute-verification) was run. No finding altered a hypothesis verdict and all
headline numbers reproduced. Confirmed items remediated:

- STAT-01: the "null-centered bootstrap ASL" reported for H1/H4/H6 was not a
  valid null test (it reduced to a Wald z over the bootstrap SD). Replaced —
  H1 now reports a permutation test of association (rho=0.812, perm p=0.001);
  H4 a Cochran-Mantel-Haenszel test (OR 3.61, CMH p~3e-178); H6 a CMH test
  (OR 1.04, CMH p=0.79). The clustered percentile CIs remain the primary
  inference. Directions unchanged.

- PREREG-04 (H7 section scope): registered §4.8 restricts matching to 3
  sections (acknowledgments / competing-declaration / author_info); the
  recall-audit matcher broadened this to 6 (adds conclusion / other /
  data_avail). Both reported: registered scope 88/5235 = 1.68%; broadened scope
  166/5235 = 3.17%. Both far under the registered <25% bound. The broadening is
  a deviation, now flagged in scan_disclosures.py.

- PREREG-05 (H6 calibration): the registered <=1% pre-2022 unverifiable-rate
  calibration is unreachable (matcher false-negative floor ~5-6% on
  legitimately-hard real refs). H6 is a relative flagged-vs-unflagged
  comparison only, not an absolute fabrication rate (verify_refs_bib.py now
  states this). Underpowered: the binary cutoff rests on ~10 papers and only
  the first 12 of ~40 references per paper are checked. Read as "no detectable
  differential at this power," not "no fabrication."

- F4 (H6 per-ref estimator): the per-ref rates reported here (flagged 4.7% /
  unflagged 5.7% / pre-2022 6.1%) are pooled-per-ref; the script also prints a
  mean-of-paper rate (5.2% / 6.3%). Both are now printed and labeled.

- C2 / M4 / M5: the sensitivity analyses (H2 KDE bandwidth sweep, specificity
  ICC, H4 monthly-strata OR) were previously computed ad hoc and recorded only
  in the lab notebook. Now committed as src/val_sensitivity.py: H2 pi_2026 =
  14-18% across bw 0.05-0.20 (trend robust); chunk-score ICC = 0.237 (chunk FPR
  4.63% vs paper 0.94%, reconciling the 2.8% passage vs 1% paper specificity);
  H4 monthly OR = 3.45 vs yearly 3.61.

- CP-1 (version dedup): the dedup regex mistook a random id of the form vNNNN
  (new-format chemrxiv-YYYY-vNNNN) for a version suffix, over-merging ~4 papers
  in papers_master (~0.01%). The regex is now guarded in build_master.py /
  country_map.py / make_figures.py / version_pairs.py. papers_master.csv as
  analyzed retains the ~4 over-merges; the effect is immaterial to every result,
  so the corpus was not rebuilt.

- Detector external validity (recalibrated): EditLens is validated in its source
  paper (arXiv 2510.03154) — multi-domain training, OOD-domain (Enron, ternary
  F1 0.904->0.866) and OOD-generator (Llama-3.3-70B ->0.850) generalization,
  robustness, and superiority over Pangram/GPTZero/Binoculars/FastDetectGPT/
  DetectAIve. Our in-domain benchmark (H1/H1a) supplies the chemistry-specific
  validation EditLens lacks. The registered §4.7 cross-detector run uses
  Pangram, which is made by the same lab (Pangram Labs) and saturates on edited
  text (AI-edited F1 43.2 vs EditLens 86.8); it is a same-lab architecture
  contrast, not independent validation, and will read lower prevalence by
  construction.

Documentation-only fixes: stale docstring counts (41,021 -> 40,212) and
score-dir paths (scores_val_bench -> scores_val_bench3); removed dead code in
build_bib_validation.py; specificity stdout relabeled (passage 2.8% vs paper 1%
FPR).

Code triage (the audit's unverified CODE findings, adjudicated by hand and
fixed): H5 secondary length-mismatch crash guard (BUG-1); H5 p is now an exact
permutation test over the 5 year points (BUG-2; rho +0.40, p=0.78, FAIL holds);
F_AI averaging repointed to the deduped chunk-count array (BUG-4; pi unchanged —
2026 generate 14.0%, substantial 32.0%, H2 PASS p<1e-4); removed a dead
group_g merge (BUG-5); H3 changepoint non-regular-asymptotics and H2
fixed-reference-density caveats noted in code (STAT-04/05). The val_mixture
consistency-check label (BUG-3) was confirmed correct, not a bug.
