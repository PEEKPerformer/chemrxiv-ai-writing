# Deviations & results log (append-only)

The registration is frozen at the GitHub releases `v1.0.0-plan` /
`v1.1.0-plan` / `v1.2.0-plan` and their Zenodo deposits; `ANALYSIS_PLAN.md`
is held byte-identical to `v1.2.0-plan` and is not edited. This file is the
**append-only** record of results and deviations: entries are added, never
reworded or removed. Authoritative timestamps are the git commit dates of
this file; the dates in entries are analysis dates (analyses ran 2026-06-10
through 2026-06-16).

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
