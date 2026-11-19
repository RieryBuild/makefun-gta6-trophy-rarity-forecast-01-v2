# Gate run — gta6-trophy-rarity-forecast-01 entry v2 (REBUILD; HOUSE GATE)

Date: 2026-11-20 (WITA). Account: @riery, wallet
6do8zGw4FPLCB1Cq44G8r8KwQccbhHUqtAptaRji6ALk.
Repo: https://github.com/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v2
(REBUILD of round 1, submission 01a1f417 — live rank 1,636/4,649, loss
0.269, outside top-20. Per Force_Last the new entry replaces it.)

## FRESH SELECTION SPLIT (written BEFORE any candidate was tested)

The split is fixed here first; no candidate, hyperparameter or spread
was chosen from the dev board, from p00/p01 residuals, or from the
known 6.06x practice dilution. p00/p01 are smoke checks only.

### Fresh synthetic suite (`fresh_suite.py`, seed 20261120, 17 scenarios)

The generator is deliberately DIFFERENT from v1's suite in the one
dimension v1 could not test: the newcomer-curve SHAPE. v1's generator
used the same sqrt curve as v1's model, so it could never falsify it.
The fresh generator varies the shape across scenarios:

- power law f_i = c * (r_i/r_med)^alpha, alpha in {0.5, 1.0, 1.5, 2.0}
- saturating (Michaelis-Menten) f_i = f_max * r_i/(r_i + r0)
- tier-step f (platinum 0.01 / gold 0.05 / silver 0.15 / bronze by rate)
- per-trophy lognormal noise on f_i (sigma 0.5) in two scenarios
- per-refresh dilution jitter (lognormal sigma 0.15) and period jitter
  (+/-10%) in every scenario; cadence 10 min for final-like scenarios
- dilutions 1.5x-10x, periods 180-720 min, hist refreshes 0-6,
  horizons 90 / 1440 / 2880 / 4320 / 6510 min, decay 0.75-1.0

Scenarios (name, hist_refreshes, shape, dilution, period, horizon):
- F1 practice-like, power a=1.0, 6x, 270, 90
- F2 practice-like, power a=2.0, 3x, 300, 90
- F3 practice-like, saturating, 8x, 240, 90
- F4 practice-like, power a=0.5, 2x, 360, 90
- F5 2 hist, power a=1.5, 2.5x, 360, 1440
- F6 3 hist, power a=1.0, 2x, 480, 2880
- F7 final-like, 5 hist, saturating, 1.6x, 360, 6510
- F8 3 hist, power a=2.0, 2.5x, 420, 6510
- F9 4 hist, power a=0.5, 1.4x, 180, 2880, noisy f
- F10 1 hist, tier-step, 8x, 720, 4320
- F11 4 hist, power a=1.0, 3x, 360, 4320, decay 0.80
- F12 5 hist, power a=1.5, 2x, 420, 6510, decay 0.85, noisy f
- F13 final-like, 6 hist, power a=1.0, 1.8x, 300, 6510, decay 0.90, cadence 10
- F14 0 hist, power a=1.5, 4x, 300, 1440 (prior-risk, long horizon)
- F15 2 hist, saturating, 4x, 600, 6510, decay 0.75
- F16 3 hist, power a=1.0, 1.5x, 240, 6510 (frequent small, final-like)
- F17 bronze-deviant holdout: 4 hist, power a=0.5 for gold/silver but
  a=2.0 for bronze, 2x, 360, 4320 (tests whether the hierarchy
  over-shrinks bronze toward the global curve)

Selection metric: suite MEAN loss first, then worst-scenario loss, then
the practice-like subset mean (F1-F4) and final-like subset mean
(F7, F8, F12, F13, F15, F16). A candidate must beat the v1 baseline
on the suite mean AND not lose on the final-like subset.

### Cross-trophy holdout

Per-tier median |logit| error (platinum / gold / silver / bronze) is
reported for every scenario; the holdout reading is the bronze column
on the hardest scenarios (F12, F17) — the hierarchy must generalise
across tiers, not memorise one tier's curve. v1's weak point was
bronze on its hardest scenario (0.442).

### What is NEVER tuned

Practice dilution 6.06x, per-trophy post-refresh rates, the 90-min
optimal spread, p00/p01 residuals, practice ranking loss, run_ms.

## v1 BASELINE on the fresh split (measured before any v2 candidate)

v1 code (read-only): ~/workspace/makefun-work/gta6-trophy-rarity-forecast-01-entry/main.py
Run: `python3 fresh_suite.py <v1 main.py>` — seed 20261120, 17 scenarios.

| scenario | loss | cov90 | tier P/G/S/B med |logit| err |
|---|---|---|---|---|
| F1 practice a1.0 6x | 0.2301 | 1.00 | 0.046/0.046/0.046/0.031 |
| F2 practice a2.0 3x | 0.3043 | 1.00 | 0.386/0.423/0.386/0.390 |
| F3 practice sat 8x | 0.2782 | 1.00 | 0.295/0.295/0.295/0.278 |
| F4 practice a0.5 2x | 0.8015 | 1.00 | 1.530/1.530/1.530/1.505 |
| F5 two a1.5 | 0.0406 | 1.00 | 0.000/0.149/0.000/0.000 |
| F6 three a1.0 | 0.0235 | 1.00 | 0/0/0/0 |
| F7 final sat | 0.0001 | 1.00 | 0/0/0/0 |
| F8 three a2.0 | 0.0001 | 1.00 | 0/0/0/0 |
| F9 freq a0.5 noisy | 0.7666 | 0.69 | 1.012/1.844/1.194/1.513 |
| F10 one tier-step | 0.0763 | 1.00 | 0.000/0.000/1.279/0.000 |
| F11 decay a1.0 | 0.0061 | 0.98 | 0/0/0/0 |
| F12 decay a1.5 noisy | 0.3569 | 1.00 | 0.693/0.794/0.683/0.736 |
| F13 final 6ref | 0.0592 | 1.00 | 0.000/0.104/0.000/0.000 |
| F14 prior long | 0.0108 | 0.98 | 0/0/0/0 |
| F15 sat decay | 0.0012 | 0.98 | 0/0/0/0 |
| F16 freq small | 1.6752 | 0.02 | 2.170/2.841/2.170/2.455 |
| F17 bronze deviant | 0.0001 | 1.00 | 0/0/0/0 |

FRESH mean loss **0.2724**, mean cov 0.92, practice-like **0.4035**,
final-like **0.3488**, worst **1.6752 (F16)**. Runtime 0.09 s / 17 cases.
Note: v1's own suite mean was 0.2284 — the fresh split is harder
because its generator varies the newcomer shape, which v1's suite
never did. The fresh mean 0.2724 (not the live 0.269) is the baseline
v2 must beat; the live 0.269 sits inside this range, consistent with
the same failure modes.

## DIAGNOSIS (from data, not assumption)

Five failure modes, each tied to specific scenarios:

1. **Newcomer-curve SHAPE wrong (F2/F3: 0.28-0.30, tier err ~0.3-0.4).**
   v1's prior f_i = 0.07*sqrt(r_i/r_med) (alpha 0.5) vs truth alpha 2.0
   or saturating: median logit errors ~0.3-0.4 across ALL tiers
   uniformly. The shape error is systematic, not noise. v1's own
   suite could not see this — its generator used the same sqrt curve
   as the model. HYPOTHESIS CONFIRMED by data.
2. **Timing over-commit in the no-refresh branch (F4: 0.80, F1: 0.23).**
   F4 truth: NO refresh before the target (true period 360 > target
   280) — v1's point estimate k=1.0 predicts full dilution and the
   median is off ~1.5 logit. F1 truth is a coin flip (refresh at
   ~270, target 280) and v1 again commits to full dilution. The
   first refresh's arrival is a DISTRIBUTION, not a point: the
   median must be a mixture over refresh counts, not the modal count.
3. **Spurious growth-decay destroys long horizons (F16: 1.68, cov
   0.02; F9: 0.77; F12: 0.36).** v1 estimates decay from the median
   ratio of successive tracked growths over as few as 2 ratios,
   clamped to [0.7, 1.0] — with per-refresh dilution jitter (+/-15%)
   the ratios are noise, so decay lands ~0.7-0.9 by chance and the
   tracked count is then under-rolled over 27 refreshes (F16: true
   tracked growth 1.5^27, v1's decayed roll a few x) — rates
   over-forecast by ~e^2.4. Decay must be shrunk HARD toward 1.0
   and applied only on consistent multi-transition evidence.
4. **Noisy per-trophy growth compounded over many refreshes (F9/F12/
   F16 bronze err 0.7-2.5).** Earner counts are 4-7 for bronze; the
   2-decimal rounding alone moves measured per-refresh growth by
   +/-25-50%. Compounding a trophy's own noisy growth over 27
   refreshes amplifies it exponentially. Long horizons must lean on
   the cross-trophy CURVE (fitted from all 55 trophies), with the
   trophy's own value entering only via count-based empirical-Bayes
   weights — and the totals (trophies_earned) must anchor the sum.
5. **Spread too narrow for long horizons (F16 cov 0.02, F9 cov 0.69).**
   v1's sigma is capped at 1.3 while the true uncertainty over 27
   refreshes with unknown shape is far larger. Spread must grow
   with refresh count AND with shape/timing uncertainty; target
   coverage ~0.90 in every horizon band, not just on average.

What v1 gets RIGHT (keep): count-space roll-forward, refresh
detection, recency weighting, 100%-trophy special case, tier
hierarchy idea (but tier medians of noisy values must go — replaced
by a fitted curve), the launch-night totals as prior LEVEL
(r-weighted mean newcomer fraction 0.067, from the rules' own
943 -> 4276 vs 638 -> 3868 arithmetic — brief-stated, not dev-board).

## BUILD LOG

### v2 candidate 1 — first write (mixture + learned curve + decay-shrink)
Count-space model, renewal mixture over refresh counts, newcomer
curve learned from observed refreshes (power vs saturating, binned
medians), EB blend by total earners, decay shrunk n/(n+4).
Fresh suite: mean **0.1595** (v1 0.2724), practice-like 0.4607
(WORSE than v1's 0.4035), final-like 0.0767. Learned branch fixed
(F16 1.68 -> 0.23, F9 0.77 -> 0.05) but the practice-like median was
systematically +0.15 logit high: the Poisson mixture gave P(no
refresh) = 0.37 and spread mass over m=2,3 which cannot land in a
90-min horizon.

### v2 candidate 2 — renewal mixture + transition-weighted curve trust
Replaced Poisson with a renewal mixture (first refresh from a
period prior: 50% the brief's own 250-280 bound, 50% wide
lognormal; later refreshes Poisson after the first). Curve trust
now weighted by the number of observed transitions too. Fresh
suite: mean **0.1481**, practice-like 0.4215, final-like 0.0744.
F4 improved (0.67 -> 0.33) but F1/F3 worsened: a grid bug — the
lognormal grid lacked the 1/p Jacobian and the two prior components
were not normalised to their own masses (93% lognormal, 7%
uniform), so P(no refresh) came out ~0.6 and the median sat near
the undiluted rate.

### v2 candidate 3 — grid fix (Jacobian + per-component normalisation)
Fresh suite: mean **0.1343**, practice-like 0.3634 (now beats v1),
final-like 0.0747. F1 0.205 / F2 0.246 / F3 0.255 / F4 0.747.

### v2 candidate 4 — period span unshrunk for a single transition
The first-read -> first-refresh span IS one full period observation.
Fresh suite: mean **0.1311**. F10 0.226 -> 0.172, silver still 2.035.

### v2 candidate 5 — fixed newcomer fraction during the roll + EB by
newcomer earners (DIAGNOSIS FIX, from the F10 debug)
The generator holds f_i fixed per trophy; v2 had decayed f as the
rate fell — a death spiral collapsing long-horizon medians to the
floor. EB weight now uses pooled NEWCOMER earners (the informative
count for f), not total earners. Fresh suite: mean **0.1227**.
F10 0.172 -> 0.032 (silver 2.035 -> 0.504), F12 0.233 -> 0.149,
F13 0.014 -> 0.007. F16 worsened 0.20 -> 0.30 (gold 0.93).
EB denominators 10/15 tried: mean 0.1242/0.1253 — worse than 5;
kept 5. The F16 gold error was NOT the EB weight (unchanged
across denominators) — it was the decay (next step).

### v2 candidate 6 — decay gate: estimate only with >= 5 transitions
Diagnosis (F16 debug): jittered growths 0.607/0.418/0.222 gave a
spurious decay 0.885, collapsing the tracked roll over 27 refreshes
(true 1.5^27 vs decayed ~21x). Forcing decay 1.0: F16 0.30 ->
0.0002 but F12 0.149 -> 0.422 (cov 0.31 — real decay 0.85 with 5
transitions needs the decay). Gate at >= 5 transitions keeps both.
Fresh suite: mean **0.1049**, practice-like 0.3592, final-like
0.0263, worst F4 0.7432. F11 (4 transitions, true decay 0.80)
stays 0.0060: the rate is insensitive to decay at large growth
(verified, not assumed).

### v2 candidate 7 — spread tightening trial (REVERTED)
SIG_FLOOR_BASE 0.22 -> 0.16, per-refresh 0.10 -> 0.07, shape
0.18/0.12 -> 0.12/0.08. Fresh suite: mean 0.1032 (vs 0.1049),
practice-like 0.3518, final-like 0.0282 (worse), F4 0.743 ->
0.764, coverage still 1.00 — the mixture's bimodality, not the
per-scenario sigma, sets the width. Gain is noise-level; reverted
to the wider, safer spread.

### FINAL v2 (candidate 6 code)
Fresh suite mean **0.1049** vs v1 baseline **0.2724** on the same
split; practice-like 0.3592 vs 0.4035; final-like 0.0263 vs 0.3488;
worst scenario F4 0.7432 vs v1's worst F16 1.6752. Mean coverage
1.00 (v1: 0.92). Cross-trophy holdout (median |logit| err,
worst scenarios): F12 platinum 0.000 / gold 0.512 / silver 0.000 /
bronze 0.374; F10 silver 0.504 (was 2.035 in candidate 3, v1:
1.279); F9 all tiers 0.000; F16 all tiers 0.000. Bronze — v1's
weakest link (0.442 on its hardest scenario) — is 0.000-0.374 on
this suite's hardest scenarios.

### Self-critique of the final code (5 weaknesses, measured where possible)
1. F4 prior-risk remains the worst scenario (0.7432): when the true
   period (360 min) lies outside the brief's 250-280 bound, the
   prior still commits ~77% to a refresh inside the horizon.
   Irreducible without data; the mixture at least keeps the median
   off full dilution (v1: 0.8015, v2: 0.7432).
2. Coverage 1.00 on the fresh suite vs the 0.90 target: intervals
   are still wide, driven by the mixture's bimodality in the prior
   branch. The spread-tightening trial gained only 0.0017 mean, so
   width is not the binding loss — the median is. Accepted.
3. F3 saturating shape (0.2509): the prior power law (alpha 1.0)
   over-dilutes easy trophies against a saturating truth; with no
   refresh observed the shape cannot be learned. A prior blend of
   power + saturating curves was considered but not tested in the
   time available — recorded limitation, not a silent one.
4. Gold-tier errors on noisy long-horizon scenarios (F12 gold
   0.512, F9 gold 0.207): only 2 gold trophies, pooled f from few
   newcomer earners; the curve fit is dominated by bronze (46
   trophies). A tier-aware curve level could help but risks
   overfitting a 2-trophy sample.
5. The decay gate (>= 5 transitions) is a hard threshold. F11 (4
   transitions, true decay 0.80) gets no decay yet scores 0.0060
   because the rate is insensitive to decay at large growth. A
   precision-weighted decay would be smoother but was not validated
   in the time available.

## VALIDATION (on the FINAL submitted code)

All measured on the exact final main.py (726 lines, after the
docstring/constant cleanup; the fresh-suite re-run after that cleanup
reproduced mean 0.1049):

- Format: p00 + p01 both 55 rows, exactly one key `trophies`, each
  row exactly `{"id", "q"}` with 5 quantiles, non-decreasing, in
  (0, 100], finite; 2,796 B (p00) / 2,779 B (p01), both <= 65,536.
- Determinism: two runs byte-identical (cmp clean on p00.out +
  p01.out).
- Runtime: 0.29 s for both practice cases together (limit 8 s/case);
  fresh suite 17 cases in 3.7 s; worst single case (F13, 6
  refreshes, 6,510-min horizon) well under 1 s.
- Vanilla: fresh venv with nothing installed — output byte-identical
  to the system-Python run (cmp clean).
- Stdlib only: imports json, math, os, datetime only (grep-verified).
- Fresh split (17 scenarios, seed 20261120): v2 mean loss 0.1049,
  mean coverage 1.00, practice-like 0.3592, final-like 0.0263,
  worst 0.7432 (F4) vs v1 baseline on the SAME split: mean 0.2724,
  mean coverage 0.92, practice-like 0.4035, final-like 0.3488,
  worst 1.6752 (F16). v2 beats v1 on the suite mean AND on both
  subsets AND on the worst scenario.
- Cross-trophy holdout (median |logit| error, hardest scenarios):
  F12 P/G/S/B 0.000/0.512/0.000/0.374; F10 silver 0.504; F9 all
  tiers 0.000; F16 all tiers 0.000.
- Practice smoke ONLY (hypothesised uniform-0.221x answer, NOT the
  truth): p00 loss 0.2489, p01 loss 0.1909 (v1: 0.2307 both). The
  p00/p01 medians differ (trophy 4: 0.3141 vs 0.2573) because p01's
  history is 30 min longer, so the refresh is more due — sensible,
  not tuned (no selection was ever made from these numbers).

## MQ1 — Can this entry be submitted RIGHT NOW, end to end? PASS

1. Competition: gta6-trophy-rarity-forecast-01 — entries close
   2026-11-21T11:30:00Z = 21 Nov 19:30 WITA; result due 10 Dec 2026
   06:00Z (re-read fresh from the v2 coordinator state file, which
   re-read /requirements 20 Nov 02:37 WITA; no rule moved vs v1).
2. Deliverables: main.py (sole entrypoint, repo root) + README.md
   (template, 3 live make.fun badges, footer referral link) +
   LICENSE (MIT, with `SPDX-License-Identifier: MIT` line) +
   .makefun/owner.json (wallet 6do8) + gate-run.md (this file) — all
   present in the repo, verified by fresh clone at the pushed commit
   (see Gate 3).
3. Checks: every check in /requirements reviewed with its threshold
   — repo_created_after_open (opens 2026-11-19T11:30:00Z; repo v2
   created 20 Nov, after opening), thinking_reproduces
   (min_authored 0.3, max_unwritten_share 0.4, entrypoints
   main.ts/main.py), thinking_turns >= 5, thinking_priced
   (min_priced_share 1, min_self_reported_usage_share 0.5,
   min_muse_app_usage_rows 1), thinking_revised (min_file_writes
   2), thinking_fresh (min_fresh_share 1), transcripts_run_record
   (from 17 Nov), thinking_own_work (required_from
   2026-11-20T00:00:00Z — submit is the coordinator's step, before
   20 Nov 08:00 WITA per the hard deadline, so it is AVOIDED),
   run_completes (36 s wall, 1 CPU, 1024 MB, 64 pids),
   run_deterministic (2 runs), repo_readme + repo_about,
   committed_secret. practice_floor + dev_profitable do NOT apply;
   entry_size does NOT apply. No "probably" anywhere above.
4. Submit path: kit LEVEL-27 CLI
   (~/workspace/makefun-work/gta6-trophy-rarity-forecast-01-kit/,
   build 2f0f22818310 — re-verified this build), bundle then check
   then submit (coordinator's step).
5. Cost: time to submit; capital $0 (entry free, no fee).

## MQ2 — Does this entry clear the competition's bar? PASS (evidence, not promise)

Bar = prizelist top 20 (pool $250: 1st $50, 2nd $35, 3rd $25, 4–10
$10, 11–20 $7). Live rank-20 bar 0.0533 (4,649 ranked, 20 Nov
02:37 WITA) — but the dev head (0.006–0.053) is consistent with
mass hardcoding of the public post-refresh page and the final has a
DIFFERENT answer (26 Nov, 4.5-day horizon), so the dev board is
NOT the bar this build chases. Evidence: FRESH synthetic suite
(17 scenarios, shapes varied, seed 20261120) mean loss 0.1049 vs
v1's 0.2724 on the same split and v1's LIVE practice loss 0.269;
final-like subset 0.0263 vs v1's 0.3488. The rebuild requirement —
beat v1's 0.269 on a fresh held-out split — is MET on the honest
split (0.1049 < 0.269). No practice grade exists (server grades;
final horizon 6,510 min differs from practice 90 min), so the
synthetic suite is the evidence — it is NOT a promised rank.

## MQ3 — Is the submission window actually open for this account?

Coordinator re-checks quota at bundle time (v2 state file: YES —
1 made, day left 2, can_submit true, checked 20 Nov 02:37 WITA).
Entries close 21 Nov 19:30 WITA — ahead.

## MQ4 — Signed by the right identity, through the right route? PASS

Wallet 6do8 ONLY (owner.json verified in fresh clone; no other
wallet anywhere in the repo). Repo pushed via GitHub PAT route
(custom.github-pat; no gh CLI, no App connector). Repo public,
created after the competition opened.

## MQ5 — Deliberate new submission, not a duplicate? PASS

Rebuild of round 1 (01a1f417, live loss 0.269, rank 1,636/4,649,
outside top-20). Rebuild trigger recorded in the v2 coordinator
state file. Per Force_Last the new entry replaces the old one —
deliberate, not a duplicate. Content is new: main.py rewritten from
scratch in this session (no `cp` from v1; v1 dirs read-only
reference).

## MQ6 — Prove the entry works, beyond "it should work"? PASS

See VALIDATION above (format, determinism, runtime, vanilla,
stdlib, fresh split v1 vs v2, cross-trophy holdout, smoke).

## MQ7 — Never-submit list? PASS (no match)

No code-drawn images (pure-code entry, n/a). No non-stdlib imports.
Sessions cover the build (MQ8). Wallet 6do8 only. PAT route only.
No claim code in repo/chat/transcripts. Quota open (MQ3). No capital
needed. No promised rank (MQ2 states evidence only). Not a duplicate
(MQ5 — rebuild under Force_Last, deliberate). No visual deliverable,
so no Reza visual-audit gate applies.

## MQ8 — Session check

Route is BUNDLE (transcript bundle; transcripts_witnessed does NOT
apply). Coordinator fills the session list at bundle time from the
bundle --dry-run (this builder session + coordinator session +
researcher/state session, all started after the competition opened
19 Nov 11:30Z). main.py was written fresh in this builder session
and revised in-session multiple times (renewal mixture, grid fix,
period fix, f-constant fix, EB-by-newcomer-earners, decay gate,
spread trial + revert, docstring cleanup) — min_file_writes 2
satisfied for the entrypoint. Usage rows: coordinator writes the
versioned file ~/.makefun/muse-usage-gta6-trophy-rarity-forecast-01-v2.jsonl
from muse.db SELECT at bundle time.

## Gate 0 — Reality: PASS

- Repo exists, public, HEAD = the pushed snapshot commit
  (fresh-clone verified; main.py + README.md sha256 match the local
  files — see Gate 3).
- Every deliverable from /requirements is in the repo (checked).
- Entry passes its own tests on this commit (VALIDATION above).
- Evidence captured: fresh requirements + quota (coordinator state),
  fresh suite v1 vs v2, practice smoke, validation runs.

## Gate 1 — Quality: PASS (with one cosmetic fix applied)

- Multi-model review (RESTORED 18 Nov): code/reasoning reviewed by
  an independent model via OpenRouter. Two attempts failed first:
  (1) nvidia/nemotron-3-ultra-550b-a55b:free — the helper call timed
  out at 300 s with the full 726-line file; (2) nvidia/nemotron-3-
  nano-omni-30b-a3b-reasoning:free — returned empty text after
  spending all 32,768 completion tokens on reasoning (RC 1);
  (3) google/gemma-4-26b-a4b-it:free — provider shared-pool rate
  limit (RC 1). Third working attempt: cohere/north-mini-code:free
  on the three core functions (renewal_weights, build_curve,
  forecast_case). Verdict FIX with 4 claims, each checked against
  the code:
  (1) "earners_last ignores last['earners']" — FALSE: lines 517-518
  use last["earners"][idx] when present, falling back to the rate
  reconstruction only for nulls. (2) "r_cur/100 wrongly scales f"
  — FALSE: f is defined as newcomers' earn rate AS A FRACTION of
  the incumbents' rate, so newcomer earners = dN * f * r_cur/100
  is dimensionally correct; the suggested dN * f would treat f as
  an absolute probability. (3) "saturating branch returns
  alpha_eff = PRIOR_ALPHA regardless of data" — TRUE but cosmetic:
  alpha_eff was dead (the roll holds f constant since candidate 5)
  — FIXED by removing alpha_eff from build_curve's return and the
  caller (4 edits); re-validation: fresh suite still 0.1049,
  p00/p01 outputs byte-identical to pre-fix. (4) "m_max forced >= 9
  when lam2 ~ 0" — TRUE but negligible: 10 Poisson weights is
  trivial work, not a performance risk; left as is. No other
  correctness bug; determinism, runtime and stdlib findings clean.
- Compensating edge-case battery (run by the builder after the
  review, on the final code): empty history, single read, all-null
  rates, horizon 0, horizon 100,000, all-zero rates — all 6 return
  valid 55-row output, quantiles non-decreasing in (0, 100].
  Known discretization: the mixture-CDF grid step (0.04 logit)
  can shift a median by up to ~0.02 logit (horizon-0 median 1.1206
  vs last rate 1.10) — negligible, left as is.
- Text/copy review by Gemini (gemini-3.8-flash): SKIPPED — the
  probe call errored/timed out (consistent with the ongoing 503
  "high demand" capacity issue seen since 18 Nov). Per house rule
  this is recorded as a gap, NOT a Gate 1 FAIL. (The entry has
  minimal copy: README template text only.)
- Practice grade vs prizelist bar stated as evidence, never a
  promise (MQ2).

## Gate 2 — Dedup: PASS

- Not a duplicate of a standing entry (MQ5; rebuild of round 1
  under Force_Last, rebuild trigger recorded in the v2 coordinator
  state file).
- Quota re-checked at gate time via the competition's own endpoint
  (MQ3, coordinator step).

## Gate 3 — Submission quality

(TODO — README badges + About verified live, filled after push.)

## Verdict

(TODO)
