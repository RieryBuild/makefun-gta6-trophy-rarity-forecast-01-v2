"""Forecast GTA VI trophy earn rates on Exophase at a future target (v2).

Generative count-space model. Exophase republishes its counts in
bursts ("refreshes"): between refreshes the page is frozen; at a
refresh the tracked-player count jumps and each trophy's earner count
grows by less, because the newcomers have earned far fewer trophies
than the incumbents. A trophy's rate is earners / tracked, both of
which move only at refreshes.

v2 differs from v1 in five places, each driven by measurements on a
fresh synthetic split (see gate-run.md):

1. The newcomer curve is LEARNED, not assumed. From every observed
   refresh the program recovers each trophy's implied newcomer earn
   fraction f_i (newcomers' earn rate / incumbents'), pools it across
   refreshes, and fits a curve of f against the trophy's rate (a power
   law and a saturating curve compete on robust residuals; the winner
   is blended toward the prior curve by how much data supports it).
   A trophy's own f_i enters only through a count-based
   empirical-Bayes weight, so bronze trophies with 4-7 earners lean
   on the curve instead of their own rounding noise.
2. The forward roll is a MIXTURE over refresh counts. The number of
   refreshes before the target follows a renewal process (the next
   refresh arrives when the page's age reaches the uncertain period;
   later ones about one period apart), so the forecast's quantiles
   are the mixture's quantiles: when a refresh inside the horizon is
   a coin flip, the median sits between the diluted and undiluted
   rates instead of committing to one of them.
3. Growth decay is shrunk HARD toward 1.0 (no decay). v1 estimated
   decay from as few as two noisy growth ratios and then compounded
   it over dozens of refreshes; v2 applies decay only when many
   transitions show it consistently.
4. The per-refresh roll holds each trophy's newcomer fraction fixed
   (it is a property of the trophy's easiness, not of the current
   rate): the rate falls because tracked players outgrow earners,
   and compounding a falling f on top of that was a death spiral
   that collapsed long-horizon forecasts to the floor.
5. Spread grows with the refresh count and with shape/timing
   uncertainty, and is not capped at v1's 1.3 logit units: long
   horizons with many refreshes ahead are genuinely uncertain.

When the history shows no refresh at all, the curve falls back to a
prior power law whose LEVEL comes from the launch-night totals in the
brief itself (newcomers earned 0.067x the incumbents' rate on
non-universal trophies) and whose dilution prior is centred on the
brief's first refresh (638 -> 3868 tracked), carried as a wide
distribution, not a point. Nothing is tuned to the dev board.

Pure standard library, deterministic, no network, no randomness.
"""

import json
import math
import os
from datetime import datetime, timezone

Z_VALUES = (-1.6448536269514722, -0.6744897501960817, 0.0,
            0.6744897501960817, 1.6448536269514722)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)

# Priors used only when the history contains no refresh to learn from,
# or to shrink a weakly supported empirical fit toward.
PRIOR_PERIOD_MIN = 270.0     # launch-night gap before the first refresh
PRIOR_TRACKED_GROWTH = 5.06  # first refresh: 638 -> 3868 tracked players
PRIOR_F_LEVEL = 0.067        # newcomers' mean earn rate, as a fraction
                             # of the incumbents', over non-universal
                             # trophies (rules totals: 943 -> 4276
                             # trophies earned vs 638 -> 3868 tracked)
PRIOR_ALPHA = 1.0            # power-law slope of the prior newcomer
                             # curve; the robust middle of the 0.5-2.0
                             # range tested on the fresh split
SIG_FLOOR_BASE = 0.22        # logit spread floor (per-scenario)
SIG_FLOOR_PER_REFRESH = 0.10
SIG_SHAPE_PRIOR = 0.18       # extra spread while the curve is a prior
SIG_SHAPE_LEARNED = 0.12     # extra spread once the curve is learned
SIGMA_CAP = 2.2


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def logit_pct(rate):
    p = clamp(rate, 0.0001, 99.9999) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit_pct(eta):
    if eta > 30.0:
        return 100.0
    if eta < -30.0:
        return 0.0
    return 100.0 / (1.0 + math.exp(-eta))


def parse_time(text):
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return None


def minutes_between(a, b):
    if a is None or b is None:
        return None
    return (b - a).total_seconds() / 60.0


def median(values):
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        return None
    mid = n // 2
    if n % 2:
        return vals[mid]
    return 0.5 * (vals[mid - 1] + vals[mid])


def round4(x):
    """Round to 4 decimals, half up, as the house baseline does."""
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value == int(value) else value


def phi(z):
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def renewal_weights(period_grid, period_med, age, horizon, cap=60):
    """Weights over the number of refreshes before the target, from a
    renewal process: the next refresh arrives when the current page
    age reaches the (uncertain) period; later refreshes arrive about
    one period apart.

    period_grid: list of (period_minutes, weight) describing the
    uncertainty in the period. age: minutes since the last refresh.
    Returns (weights, first_m) with weights[i] = P(count = first_m+i).
    """
    if horizon <= 0:
        return [1.0], 0
    p0 = 0.0
    num = 0.0
    den = 0.0
    for period, w in period_grid:
        if period > age + horizon:
            p0 += w
        else:
            num += w * (period - age)
            den += w
    p0 = clamp(p0, 0.0, 1.0)
    if den <= 0:
        return [1.0], 0
    exp_first = num / den
    lam2 = max(0.0, (horizon - exp_first) / max(period_med, 1.0))
    # Poisson weights for the ADDITIONAL refreshes after the first.
    m_max = int(lam2 + 6.0 * math.sqrt(lam2 + 1.0) + 3.0)
    m_max = min(max(m_max, 0), cap - 1)
    add = [math.exp(-lam2)]
    for m in range(1, m_max + 1):
        add.append(add[-1] * lam2 / m)
    total_add = sum(add)
    add = [x / total_add for x in add]
    weights = [p0] + [(1.0 - p0) * x for x in add]
    # Cut negligible tails.
    lo = 0
    cum = 0.0
    while lo < len(weights) - 1 and cum + weights[lo] < 0.0005:
        cum += weights[lo]
        lo += 1
    hi = len(weights) - 1
    cum = 0.0
    while hi > lo and cum + weights[hi] < 0.0005:
        cum += weights[hi]
        hi -= 1
    weights = weights[lo:hi + 1]
    total = sum(weights)
    return [x / total for x in weights], lo


def period_prior_grid():
    """Prior over the refresh period (minutes) for the no-refresh
    branch: half the mass on the brief's own bound for the first
    refresh (unchanged through the 04:00 read, refreshed by 04:30,
    i.e. a period of 250-280 minutes from the 23:50 start), half on
    a wide lognormal around 270 in case the cadence has changed.
    Each component is normalised to its own mass; grid weights use
    the lognormal density in period space (with the 1/p Jacobian),
    so a uniform-in-period grid does not overweight the long tail."""
    grid = []
    uni = [float(p) for p in range(250, 281, 5)]
    for p in uni:
        grid.append((p, 0.5 / len(uni)))
    dens = []
    for p in range(120, 721, 30):
        d = math.exp(-0.5 * ((math.log(p) - math.log(270.0)) / 0.45) ** 2) / p
        dens.append((float(p), d))
    total = sum(d for _, d in dens)
    for p, d in dens:
        grid.append((p, 0.5 * d / total))
    return grid


def period_learned_grid(period_est):
    """Period uncertainty once refreshes have been observed: lognormal
    around the estimated period (sigma 0.25 in log space), weighted
    with the 1/p Jacobian."""
    grid = []
    dens = []
    for p in range(120, 901, 30):
        d = math.exp(-0.5 * ((math.log(p) - math.log(period_est)) / 0.25) ** 2) / p
        dens.append((float(p), d))
    total = sum(d for _, d in dens)
    for p, d in dens:
        grid.append((p, d / total))
    return grid


def poisson_weights(mean, cap=60):
    """Poisson pmf weights for counts 0..M, renormalised (M covers the
    mass to ~6 sigma above the mean). Returns (weights, first_m):
    weights[i] is P(count = first_m + i); negligible tails are cut so
    long-horizon cases stay fast."""
    if mean <= 0:
        return [1.0], 0
    m_max = int(mean + 6.0 * math.sqrt(mean + 1.0) + 3.0)
    m_max = min(max(m_max, 1), cap)
    w = [math.exp(-mean)]
    for m in range(1, m_max + 1):
        w.append(w[-1] * mean / m)
    total = sum(w)
    w = [x / total for x in w]
    # Cut tails holding under 0.05% of the mass on either side.
    lo = 0
    cum = 0.0
    while lo < len(w) - 1 and cum + w[lo] < 0.0005:
        cum += w[lo]
        lo += 1
    hi = len(w) - 1
    cum = 0.0
    while hi > lo and cum + w[hi] < 0.0005:
        cum += w[hi]
        hi -= 1
    w = w[lo:hi + 1]
    total = sum(w)
    return [x / total for x in w], lo


def analyse_history(case):
    """Parse the history into reads and refresh transitions.

    Earner counts are reconstructed from the rates and the tracked
    count, then rescaled so their sum matches the page's
    `trophies_earned` total, which removes part of the 2-decimal
    rounding error. A transition is a read where the tracked count
    (or any rate) moved. Each transition records the implied
    newcomer earn fraction per trophy.
    """
    history = case.get("history") or []
    trophies = case.get("trophies") or []
    n_troph = len(trophies)
    reads = []
    for entry in history:
        rates = entry.get("rates") or []
        if len(rates) < n_troph:
            continue
        moment = parse_time(entry.get("at") or entry.get("slot") or "")
        tracked = entry.get("players_tracked")
        if not isinstance(tracked, (int, float)) or tracked <= 0:
            continue
        tracked = float(tracked)
        earners = []
        for r in rates:
            if isinstance(r, (int, float)):
                earners.append(max(0.0, float(r)) * tracked / 100.0)
            else:
                earners.append(None)
        total = entry.get("trophies_earned")
        known = [e for e in earners if e is not None]
        if (isinstance(total, (int, float)) and total > 0 and known
                and sum(known) > 0):
            scale = float(total) / sum(known)
            if 0.5 < scale < 2.0:
                earners = [None if e is None else e * scale
                           for e in earners]
        reads.append({"moment": moment, "tracked": tracked,
                      "rates": list(rates), "earners": earners})
    if not reads:
        return None, [], None
    transitions = []
    for prev, cur in zip(reads, reads[1:]):
        n_prev, n_cur = prev["tracked"], cur["tracked"]
        changed = abs(n_cur - n_prev) > 0.005 * n_prev
        if not changed:
            for a, b in zip(prev["rates"], cur["rates"]):
                if (isinstance(a, (int, float))
                        and isinstance(b, (int, float))
                        and abs(b - a) > 0.02):
                    changed = True
                    break
        if not changed:
            continue
        fracs = []
        deltas = []
        for e_prev, e_cur in zip(prev["earners"], cur["earners"]):
            if e_prev is None or e_cur is None:
                fracs.append(None)
                deltas.append(None)
                continue
            deltas.append(e_cur - e_prev)
            d_n = n_cur - n_prev
            if d_n <= 0 or e_prev <= 0:
                fracs.append(None)
                continue
            r_prev = 100.0 * e_prev / n_prev
            f = (e_cur - e_prev) / (d_n * r_prev / 100.0)
            fracs.append(clamp(f, 0.0, 1.2))
        transitions.append({
            "moment": cur["moment"],
            "tracked_growth": n_cur / n_prev - 1.0,
            "log_tracked_growth": math.log(n_cur / n_prev),
            "fracs": fracs,
            "earner_deltas": deltas,
            "d_tracked": n_cur - n_prev,
        })
    moments = [t["moment"] for t in transitions if t["moment"] is not None]
    period = None
    if len(moments) >= 2:
        diffs = [minutes_between(a, b) for a, b in zip(moments, moments[1:])]
        diffs = [d for d in diffs if d is not None and d > 0]
        period = median(diffs) if diffs else None
    elif len(moments) == 1 and reads[0]["moment"] is not None:
        period = minutes_between(reads[0]["moment"], moments[0])
    return reads[-1], transitions, period


def fit_power_curve(points):
    """Fit log f = a + b * log(r / r_med) to (rate, f) points by binned
    medians: bin by log-rate, take each bin's median point, slope from
    the median pairwise slope (Theil-Sen), intercept from the median
    residual. Returns (a, b, n_points) or None."""
    if len(points) < 8:
        return None
    pts = sorted(points)
    nbins = 5
    bins = [[] for _ in range(nbins)]
    for k, p in enumerate(pts):
        bins[min(nbins - 1, k * nbins // len(pts))].append(p)
    meds = []
    for b in bins:
        if not b:
            continue
        xs = sorted(p[0] for p in b)
        ys = sorted(p[1] for p in b)
        meds.append((median(xs), median(ys)))
    if len(meds) < 3:
        return None
    slopes = []
    for i in range(len(meds)):
        for j in range(i + 1, len(meds)):
            dx = meds[j][0] - meds[i][0]
            if abs(dx) > 0.05:
                slopes.append((meds[j][1] - meds[i][1]) / dx)
    if not slopes:
        return None
    b = clamp(median(slopes), 0.0, 3.0)
    a = median([y - b * x for x, y in meds])
    return (a, b, len(points))


def build_curve(rates_last, earners_last, transitions, r_med, n_trans):
    """Return (curve_fn, learned_flag).

    curve_fn(rate_pct) -> newcomer fraction f for a trophy currently
    at that rate. Learned from observed refreshes when possible,
    otherwise the prior power law. The level is always anchored so
    the earner-weighted mean f over non-universal trophies matches
    the observed (or prior) level.
    """
    n_troph = len(rates_last)
    # Pool each trophy's implied f across transitions, weighted by the
    # number of newcomers in each transition.
    pooled = [None] * n_troph
    for i in range(n_troph):
        num = 0.0
        den = 0.0
        for t in transitions:
            f = t["fracs"][i] if i < len(t["fracs"]) else None
            if f is None:
                continue
            w = max(t["d_tracked"], 1.0)
            num += w * f
            den += w
        if den > 0:
            pooled[i] = num / den
    points = []
    for i in range(n_troph):
        r = rates_last[i]
        f = pooled[i]
        if f is None or r is None or r >= 99.995 or r <= 0 or f <= 0:
            continue
        points.append((math.log(max(r, 0.05) / max(r_med, 0.05)),
                       math.log(f), r, f))
    # Candidate 1: power law on binned medians.
    pow_fit = fit_power_curve([(x, y) for x, y, _, _ in points])
    # Candidate 2: saturating curve, grid over the knee r0.
    sat_fit = None
    if len(points) >= 8:
        best = None
        for r0 in (0.5, 1.0, 1.5, 2.5, 4.0):
            fs = [f * (r + r0) / r for _, _, r, f in points]
            f_level = median(fs)
            if f_level is None or f_level <= 0:
                continue
            resid = median([abs(math.log(max(f, 1e-4))
                                - math.log(max(f_level * r / (r + r0), 1e-4)))
                            for _, _, r, f in points])
            if best is None or resid < best[0]:
                best = (resid, f_level, r0)
        if best is not None:
            sat_fit = (best[1], best[2], best[0])
    # Robust residuals decide between the candidates.
    def _pow_resid():
        if pow_fit is None:
            return None
        a, b, _ = pow_fit
        return median([abs(y - (a + b * x)) for x, y, _, _ in points])
    pow_resid = _pow_resid()
    sat_resid = sat_fit[2] if sat_fit else None
    use_sat = (sat_fit is not None
               and (pow_resid is None or sat_resid < pow_resid))
    n_pts = len(points)
    # Blend the empirical curve toward the prior curve by how much
    # data supports it: more pooled trophies AND more observed
    # refreshes both raise the weight. A single refresh (however many
    # trophies) cannot carry the shape on its own.
    w_emp = (n_pts / (n_pts + 15.0) if n_pts else 0.0)
    w_emp *= n_trans / (n_trans + 2.0) if n_trans else 0.0
    # Prior curve in log space: f = C * (r / r_med) ** PRIOR_ALPHA,
    # with C set below by the level anchor.
    # Empirical level: earner-weighted mean f over the pooled points.
    if n_pts:
        num = sum(f * r for _, _, r, f in points)
        den = sum(r for _, _, r, f in points)
        emp_level = num / den if den > 0 else PRIOR_F_LEVEL
    else:
        emp_level = PRIOR_F_LEVEL
    level = (w_emp * emp_level + (1.0 - w_emp) * PRIOR_F_LEVEL)
    if use_sat:
        f_sat_level, r0, _ = sat_fit
        # The prior saturating level: a curve whose earner-weighted
        # mean equals `level` has F ~ level / E[r/(r+r0)] ~= 4*level
        # for the observed rate range; blend toward that.
        sat_level = (w_emp * f_sat_level
                     + (1.0 - w_emp) * (level * 4.0))
        def curve_sat(r):
            if r >= 99.995:
                return 1.0
            return clamp(sat_level * max(r, 0.05)
                         / (max(r, 0.05) + r0), 0.005, 0.95)
        return curve_sat, True
    if pow_fit is not None:
        a_emp, b_emp, _ = pow_fit
        b = w_emp * b_emp + (1.0 - w_emp) * PRIOR_ALPHA
    else:
        b = PRIOR_ALPHA
    # Anchor C so the earner-weighted mean f equals `level`.
    num = 0.0
    den = 0.0
    for r in rates_last:
        if r is None or r >= 99.995 or r <= 0:
            continue
        wgt = (max(r, 0.05) / max(r_med, 0.05)) ** b
        num += wgt * r
        den += r
    c_level = level / (num / den) if num > 0 and den > 0 else level

    def curve_pow(r):
        if r >= 99.995:
            return 1.0
        return clamp(c_level * (max(r, 0.05) / max(r_med, 0.05)) ** b,
                     0.005, 0.95)

    return curve_pow, (pow_fit is not None)


def forecast_case(case):
    trophies = case.get("trophies") or []
    n_troph = len(trophies)
    horizon = float(case.get("horizon_minutes") or 0.0)
    checkpoint = parse_time(case.get("at") or "")
    history = case.get("history") or []
    last, transitions, period_obs = analyse_history(case)

    if last is None:
        return [{"id": t.get("id"), "q": [0.05, 0.2, 0.5, 2.0, 8.0]}
                for t in trophies]

    n_last = last["tracked"]
    rates_last = []
    for idx in range(n_troph):
        r = None
        for read in reversed(history):
            rates = read.get("rates") or []
            if idx < len(rates) and isinstance(rates[idx], (int, float)):
                r = float(rates[idx])
                break
        rates_last.append(r if r is not None else 0.0)
    earners_last = []
    for idx, r in enumerate(rates_last):
        e = None
        if last["earners"][idx] is not None:
            e = last["earners"][idx]
        else:
            e = clamp(r, 0.0, 100.0) * n_last / 100.0
        earners_last.append(max(0.0, e))
    numeric_rates = sorted(r for r in rates_last
                           if isinstance(r, (int, float)) and r < 99.995)
    r_med = median(numeric_rates) if numeric_rates else 0.78

    first_moment = None
    if history:
        first_moment = parse_time(history[0].get("at")
                                  or history[0].get("slot") or "")
    last_change_at = None
    prev_n = None
    for entry in history:
        moment = parse_time(entry.get("at") or entry.get("slot") or "")
        n_here = entry.get("players_tracked")
        if prev_n is not None and n_here != prev_n and moment is not None:
            last_change_at = moment
        prev_n = n_here

    if transitions:
        # --- Learned branch: refresh process from the transitions. ---
        recent = transitions[-3:]
        log_growths = [t["log_tracked_growth"] for t in recent]
        g_med = median(log_growths)
        if g_med is None or g_med < 0:
            g_med = math.log1p(0.2)
        growth = math.expm1(g_med)
        # Period: the span from the first read to the first refresh IS
        # one full period observation, so use it directly when it is
        # the only one; with two or more inter-refresh gaps, shrink
        # their median toward the prior on the log scale.
        if period_obs is not None and period_obs > 0:
            if len(transitions) <= 1:
                period = period_obs
            else:
                n_gaps = len(transitions) - 1
                w = n_gaps / (n_gaps + 1.0)
                period = math.exp(w * math.log(period_obs)
                                  + (1.0 - w) * math.log(PRIOR_PERIOD_MIN))
        else:
            period = PRIOR_PERIOD_MIN
        # Decay: estimated ONLY with >= 5 observed transitions. With
        # fewer, a declining growth sequence is as likely to be
        # per-refresh dilution jitter as real decay, and extrapolating
        # it over dozens of future refreshes collapses the tracked
        # roll (F16: 3 transitions, spurious decay 0.885, tracked
        # 1.5^27 vs a decayed ~21x). With >= 5 transitions a
        # consistent decline is evidence (F12: 5 transitions, true
        # decay 0.85); the slope is still shrunk toward 1.0.
        decay = 1.0
        all_logs = [t["log_tracked_growth"] for t in transitions]
        if len(all_logs) >= 5:
            slopes = []
            for a, b in zip(all_logs, all_logs[1:]):
                if a > 0.02:
                    slopes.append((b - a) / a)
            if slopes:
                raw = median(slopes)
                n_pairs = len(slopes)
                shrunk = raw * n_pairs / (n_pairs + 4.0)
                decay = clamp(1.0 + shrunk, 0.90, 1.0)
        # Page age since the last refresh.
        age = 0.0
        if last_change_at is not None and checkpoint is not None:
            age = minutes_between(last_change_at, checkpoint) or 0.0
        weights, m_lo = renewal_weights(
            period_learned_grid(period), period, age, horizon)
        sig_shape = SIG_SHAPE_LEARNED
        learned = True
    else:
        # --- Prior branch: no refresh observed. ---
        period = PRIOR_PERIOD_MIN
        growth = PRIOR_TRACKED_GROWTH
        decay = 1.0
        age = minutes_between(first_moment, checkpoint) or 0.0
        weights, m_lo = renewal_weights(
            period_prior_grid(), period, age, horizon)
        sig_shape = SIG_SHAPE_PRIOR
        learned = False

    curve, _curve_learned = build_curve(
        rates_last, earners_last, transitions, r_med, len(transitions))

    # Per-trophy newcomer fraction: own pooled value blended toward
    # the curve with a count-based empirical-Bayes weight. The
    # informative count for f is the number of NEWCOMER earners
    # (earners gained across the observed refreshes), not the total
    # earners: a trophy whose refreshes added 20 earners pins its f
    # far better than one that added 1, whatever its total.
    pooled = [None] * n_troph
    pooled_new = [0.0] * n_troph
    for i in range(n_troph):
        num = 0.0
        den = 0.0
        new_tot = 0.0
        for t in transitions:
            f = t["fracs"][i] if i < len(t["fracs"]) else None
            d = t["earner_deltas"][i] if i < len(t["earner_deltas"]) else None
            if d is not None and d > 0:
                new_tot += d
            if f is None:
                continue
            w = max(t["d_tracked"], 1.0)
            num += w * f
            den += w
        if den > 0:
            pooled[i] = num / den
        pooled_new[i] = new_tot
    f_trophy = []
    for i in range(n_troph):
        r = rates_last[i]
        c = curve(r)
        if pooled[i] is None:
            f_trophy.append(c)
        else:
            w = pooled_new[i] / (pooled_new[i] + 5.0)
            f_trophy.append(w * pooled[i] + (1.0 - w) * c)

    m_max = m_lo + len(weights) - 1

    # Per-refresh tracked multipliers (decay applies to the growth).
    tracked_mult = [1.0]
    for j in range(m_max):
        tracked_mult.append(tracked_mult[-1]
                            * (1.0 + growth * (decay ** j)))

    rows = []
    for idx, trophy in enumerate(trophies):
        rate = clamp(float(rates_last[idx]), 0.0, 100.0)
        earners0 = earners_last[idx]
        if rate >= 99.995:
            quantiles = [99.99, 99.995, 100.0, 100.0, 100.0]
            rows.append({"id": trophy.get("id"), "q": quantiles})
            continue
        # Scenario centres and spreads, one per refresh count m.
        centres = []
        sigmas = []
        for m in range(m_lo, m_max + 1):
            n_t = n_last * tracked_mult[m]
            e_t = earners0
            r_cur = rate
            n_cur = n_last
            for j in range(m):
                g_j = growth * (decay ** j)
                n_next = n_cur * (1.0 + g_j)
                # A trophy's newcomer fraction is a property of the
                # trophy (its easiness), fixed across refreshes: it
                # does NOT fall as the rate falls. The rate falls
                # because tracked players outgrow earners, not
                # because newcomers stop earning the trophy.
                f_j = f_trophy[idx]
                e_t = e_t + (n_next - n_cur) * f_j * r_cur / 100.0
                n_cur = n_next
                r_cur = 100.0 * e_t / n_cur if n_cur > 0 else r_cur
            centre = clamp(100.0 * e_t / n_t if n_t > 0 else rate,
                           0.001, 99.99)
            sig_count = 0.8 / math.sqrt(max(e_t, 1.0))
            sig_floor = SIG_FLOOR_BASE + SIG_FLOOR_PER_REFRESH * math.sqrt(m)
            sigma = math.sqrt(sig_floor ** 2 + sig_count ** 2
                              + sig_shape ** 2)
            sigma = min(sigma, SIGMA_CAP)
            centres.append(centre)
            sigmas.append(sigma)
        # Mixture quantiles by inverting the mixture CDF on a logit grid.
        grid_lo, grid_hi, step = -10.0, 6.0, 0.04
        n_grid = int((grid_hi - grid_lo) / step) + 1
        grid = [grid_lo + k * step for k in range(n_grid)]
        logits = [logit_pct(c) for c in centres]
        cdf = []
        for x in grid:
            s = 0.0
            for w, mu, sg in zip(weights, logits, sigmas):
                s += w * phi((x - mu) / sg)
            cdf.append(s)
        quantiles = []
        for tau in LEVELS:
            pick = grid[-1]
            for k in range(n_grid):
                if cdf[k] >= tau:
                    pick = grid[k]
                    break
            quantiles.append(round4(clamp(inv_logit_pct(pick), 0.001, 100.0)))
        for j in range(1, 5):
            if quantiles[j] < quantiles[j - 1]:
                quantiles[j] = quantiles[j - 1]
        rows.append({"id": trophy.get("id"), "q": quantiles})
    return rows


def run():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(in_dir) if n.endswith(".in"))
    for name in names:
        case_id = name[:-3]
        with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        rows = forecast_case(case)
        payload = {"trophies": rows}
        blob = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        with open(os.path.join(out_dir, case_id + ".out"), "wb") as fh:
            fh.write(blob)


if __name__ == "__main__":
    run()
