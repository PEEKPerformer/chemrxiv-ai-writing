# Registered analysis plan

A ChemRxiv study of AI-assisted writing based on a full-text corpus spanning 2017-2026. Registered 2026-06-10; the git commit introducing this file is the timestamp. Any deviations will be logged in this file with dates.

## 1. Status disclosure

The analyses in section 4 are registered before being run. As of this
registration:

- All of the captured 59,513 corpus texts have been scored by both detectors, and the
  results in section 3 have been observed. The results are disclosed and will not be considered for hypothesis-testing purposes.
- The validation benchmark rewrites modeled after EditLens methodology (section 4.1) are being generated.
  No detector score of any rewrite exists as of this writing.
- The author-level panel, mixture prevalence estimator, changepoint
  model, homogenization analysis, reference-verification arm, and
  Pangram API replication have not been run in any form.

## 2. Frozen design elements

These choices were made before this registration and will not change.

- OpenAlex snapshot of ChemRxiv (source S4393918830) through
  2026-05-18: 59,876 DOIs, 59,519 retrieved full texts, 59,513 cleaned.
  One paper per base DOI, keeping the latest posted version: 40,212
  papers.
- EditLens RoBERTa-large (primary) and EditLens
  Llama-3.2-3B (cross-check), pinned revisions, inference replicating
  the reference implementation. Paper score is calculated as length-weighted mean of
  chunk scores over exclusive word spans.
- The 99th percentile of each detector's
  paper-level score distribution on papers posted 2017-2021: 0.087
  (RoBERTa), 0.114 (Llama), as computed by `src/build_master.py`. These
  define entries as "flagged" everywhere below.
- For a rewrite of a benchmark passage, 1 minus the
  difflib.SequenceMatcher ratio between the normalized word sequences of
  original and rewrite (`src/val_pack.py`).
- Two-sided tests at alpha = 0.05.
  Proportion CIs are Wilson 95%. Resampling CIs use cluster bootstrap
  with 1,000 replicates; the clustering unit is named per analysis. Each
  numbered confirmatory analysis has one primary hypothesis; everything
  else it produces is secondary and will be labeled descriptive.

## 3. Results already observed (exploratory, disclosed)

On 2026-06-09 through 2026-06-10, before this registration the yearly flagged share was shown to rise from a baseline of 0.5-1.5% pre-2022 to 46.0% (RoBERTa) and 48.9% (Llama) in early 2026. Cross detector agreement was shown to be r = 0.909. Section level rises were shown highest in discussion, conclusion, and abstract; smallest in methods. Group-calibrated flag rates derived from OpenAlex affiliation of 47.3% (non-anglophone) vs. 24.5% (anglophone). No citation penalty was observed in year-by-topic strata. Country-observed/expected ratios after subfield standardization (e.g. China 1.55). Partial-use intensity distributions. Rise-then-fall trajectory of known marker words (e.g. Delve). Where the manuscript reports these, it will mark them as observed before registration.

## 4. Confirmatory analyses (not yet run)

### 4.1 Validation benchmark

1,000 pre-2022 passages (one per paper, stratified per section) rewritten by five open-weight models (Gemma-4-12B-it, Qwen3.6-27B, GLM-4.7-Flash, gpt-oss-20b, Qwen2.5-7B-Instruct) at three different intensities (polish, rewrite, and generation from a shared LLM-generated fact sheet). None of these five models appear in EditLens training data which contains no scientific text.

The primary hypothesis (H1) is that RoBERTa paper-level score increases with
  measured edit fraction: Spearman correlation > 0 across all variants,
  p < 0.05, clustered by source passage.


Sensitivity at our 0.087 threshold will be reported per generator-by-treatment cell with Wilson CIs; specificity will be reported on the 1,000 untouched pre-2022 originals. A pooled logistic model (flagged ~ treatment + generator + section + edit fraction) will be used to check heterogeneity.

EditLens reports relatively robust LLM-agnostic transfer. We will measure generate-treatment sensitivity between the three 2026 generators (Gemma-4,
  Qwen3.6, GLM-4.7) and the 2024 control (Qwen2.5-7b) with CI. We will claim transfer holds if the pooled 2026-sensitivity is within 10 percentage points below the control, or higher.


All corpus prevalence figures in the eventual manuscript will be accompanied by sensitivity-corrected estimates using the sensitivities measured by our LLM rewrite corpus (polish, rewrite, generate). If the generate sensitivity is <50%, the threshold prevalence will be presented as a lower-bound; mixture estimate will become the headline number.

Amendment 2026-06-10: two Llama generators (Llama-3.1-8B-Instruct, Llama-3.2-3B-Instruct) added before any rewrite was scored. Llama was originally excluded because the cross-check detector is Llama-3.2 based; these cells deliberately measure that self-detection bias (RoBERTa as neutral reference; Llama-3.2-3B is the cross-check detector's own base model) and add a widely-deployed 2024-era control. Not part of H1/H1a; reported separately, no hypothesis.

Result 2026-06-12: H1 PASS — Spearman(score, edit_frac)=0.812 (passage-clustered bootstrap 95% 0.803-0.821). H1a transfer HOLDS — 2026 trio generate-sensitivity 97.0% vs 2024 control 98.1%, diff -1.1 pp (within the -10 pp margin). Consequence rule not triggered (generate-sensitivity 95-99%). Specificity: 28/1000 originals flagged (2.8%, passage-level; paper-level FPR stays 1% by threshold construction). Deviation: a QC audit found generation-time token/markdown contamination (gemma4 special tokens + reasoning channel, llama32 preamble, gptoss markdown); outputs were normalized (src/clean_rewrites.py, raw backed up) and the benchmark re-scored. Bootstrap p-values use a null-centered statistic (prior mean(boots<=null) was invalid).

### 4.2 Mixture prevalence

The paper-level score distribution is modeled as a mixture of pooled 2017-2021 empirical distribution and an AI-influenced component which is estimated from benchmark variants; mixing weight estimated by maximum likelihood. The output is a yearly weight with paper-clustered bootstrap CI. 

H2: The 2025 weight exceeds 2022 weight, p<0.05. A consistency check will be performed to ensure weight does not fall below the same year's flagged share.

Result + deviation 2026-06-12: H2 PASS — π_2025 8.0% vs π_2022 0.2% (generate F_AI), two-sample bootstrap p<0.0001. Deviation: the registered consistency check (π ≥ flag rate) does not hold — π < flag rate every year, because F_AI is predominantly-AI text (π estimates predominant-AI prevalence) while the flag rate counts any threshold crossing. Prevalence reported as a bracket: predominant-AI 14.5% / substantial 32% / any-detectable 46% (2026). Continuous-dose mixture not implemented.



### 4.3 Changepoint

The segmented binomial regression of monthly flagged counts on posting month, a single breakpoint scored by profile likelihood from 2017-01 through 2026-05. H3: the breakpoint's 95% CI contains 2022-12, the first full month after the general release of ChatGPT as a consumer product.

Result 2026-06-12: H3 FAIL — breakpoint MLE 2022-01, 95% CI 2021-09..2022-06, excludes 2022-12. Cause: a single broken line cannot fit a convex multi-year rise; the kink is placed early. Model not changed. Exploratory (non-registered) onset = first 3-consecutive-month run above the pre-2022 floor upper-95% bound = 2023-06.

### 4.4 Author-level adoption panel

Cohort: OpenAlex author IDs with at least two corpus papers posted
2017-2022 and at least two posted 2023-2026. Papers are assigned to
authors by OpenAlex authorship. 

H4: Among cohort authors' 2023-2026 papers ordered by date,
P(next paper flagged | current paper flagged) exceeds P(next paper
flagged | current paper not flagged), within posting year, by
Mantel-Haenszel test, clustered bootstrap by author. Secondary,
descriptive: time from 2022-12 to each author's first flagged paper by
affiliation group and subfield; within-author change in high-score word
fraction between first and subsequent flagged papers.

### 4.5 Prose homogenization

Per-paper feature vector: relative frequencies of the 200 most common
words in the pooled 2017-2021 corpus, computed on each paper's cleaned
text. 

Dispersion per posting year: mean pairwise cosine distance among
1,000 randomly sampled papers (seed 20260610). 

**Primary hypothesis
(H5):** dispersion declines from 2022 to 2026, the Spearman correlation of
the five yearly values with year < 0, bootstrap p < 0.05. Secondary,
descriptive: the same statistics computed within flagged and unflagged papers
separately.

Result 2026-06-12: H5 FAIL — Spearman(year, dispersion)=+0.40 (wrong sign),
bootstrap p=0.95. Dispersion 0.092/0.089/0.092/0.092/0.101 (2022-26). n=5
yearly points; common-word (top-200) profile only.

### 4.6 Reference verification

Reference strings will be parsed from the raw text beyond each paper's reference onset. References carrying a DOI will be resolved using the crossref API and checked for a) existence and b) title agreement with the cited string; references without a DOI will be matched by crossref bibliographic query. A reference will be considered "unverifiable" if no match scores above a cutoff chosen such that at most 1% of pre-2022 references come out unverifiable (the pre-LLM corpus calibrates the checker's false-flag floor the same way it calibrates the detectors). H6: among 2023-2026 papers, flagged paper will have a higher unverifiable reference rate than unflagged papers within a particular posting year; Mantel-Haenszel tested, clustered bootstrap by paper. Both directions will be reported as a null is informative here.

Result + deviation 2026-06-12: DOI-existence channel run (src/parse_references.py). Inconclusive — pre-2022 unverifiable-DOI rate 24% (PDF-extraction noise, not fabrication); calibration cutoff →100%, MH undefined. Raw means: flagged 22.7% vs unflagged 16.0% (noise-dominated, confounded). Deviation: registered non-DOI bibliographic-query channel (Crossref query.bibliographic) not implemented; required to test H6. H6 untested, not null.

### 4.7 Pangram API replication

A $5,000 API credits grant has been issued by Pangram Labs to aid in the completion of this study. The primary end-point of AI detection will be re-run on the commercial API and compared to the results of models used in the study: paper-level Pearson r against the RoBERTa score, and yearly flagged-share differences at Pangram's own threshold. No hypothesis.

### 4.8 Disclosure gap (added by amendment 2026-06-10)

Added after the original registration but before any disclosure scan was run. The flagged/unflagged labels used here come from corpus scores that already existed at registration; the disclosure side is what is being pre-specified.

Acknowledgment, declaration, and author-info sections will be scanned for AI-use disclosure statements. Matching is restricted to those sections and to disclosure-shaped phrases (e.g. "ChatGPT was used to improve the language"), not bare model-name mentions, so papers that merely study LLMs are not counted. The pattern list will be frozen in `src/scan_disclosures.py` at first run, calibrated the same way as everywhere else in this study: no pre-2022 paper disclosed LLM writing assistance, so the pattern set must produce <0.5% hits on the pre-2022 corpus. A sample of matches will be human-validated.

H7: among 2024-2026 flagged papers, fewer than 25% carry any AI-use disclosure (Wilson CI). Secondary, descriptive: disclosure rate by year, affiliation group, and flagged status.

Matcher deviations 2026-06-12 (matcher refined over three passes):
1. Negative declarations ("no AI was used") split to their own tier (bug, not a threshold change): 2.27%→2.25%.
2. Sample validation: false positives "curie" (Curie-Weiss/Institut Curie), "claude" (Univ. Claude Bernard Lyon), AI-term+writing-word matching citations/titles. Required a disclosure frame: 2.25%→1.60%.
3. Recall audit: frame-only missed passive voice and non-acknowledgment sections. Final matcher = AI-term AND use-frame (incl. passive) AND writing-object term, over {acknowledgments, competing, author_info, conclusion, other, data_avail}, with a BOILER_NEG guard: 1.60%→3.17%.

Result (final): H7 = 166/5,235 flagged 2024-26 papers disclose = 3.17% (Wilson 2.73-3.68); unflagged 0.85%. Pre-2022 calibration 0.00%; sample precision ~92%. < 25% → registered prediction holds. Superseded values: 1.60% (under-recall), 3.84% (under-precision interim).

## 5. What this plan does not cover

Exploratory analysis not covered by this list may appear in the manuscript and will be labeled as such. Figure-caption arm and revision analysis await data that is not available yet and may be subject to change.

## 6. AI-assistance disclosure

Portions of this repository's code and documentation, including the first draft of this plan, were produced with AI assistance (Claude, Anthropic). All analyses, design decisions, and final text were reviewed, edited, and approved by the authors. The same disclosure will appear in the manuscript. Given the subject of this study we consider disclosed AI assistance the appropriate standard, and we note for the record that a commercial detector (Pangram 3.3.2, 2026-06-10) run on this document correctly separated the AI-drafted sections from the author-rewritten ones.
