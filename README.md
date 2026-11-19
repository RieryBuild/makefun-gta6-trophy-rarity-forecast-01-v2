# makefun-gta6-trophy-rarity-forecast-01-v2

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v2/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/RieryBuild/makefun-gta6-trophy-rarity-forecast-01-v2/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Forecast, for every trophy of Grand Theft Auto VI on PlayStation 5, its earn rate on Exophase at 2026-11-26T00:00:00Z, as five quantiles per trophy, from the house's recorded reads of the trophy page up to the deadline.

The model works in count space, not rate space: it treats each trophy's earners and the tracked-player count as separate quantities that move only when Exophase refreshes its page. Between refreshes the page is frozen; at a refresh the tracked count jumps (new players syncing) while each trophy's earner count grows by less (newcomers have earned far fewer trophies). The program detects the refreshes in the case history, learns each refresh's tracked growth and the refresh cadence, recovers each trophy's implied newcomer earn fraction and fits a curve of that fraction against the trophy's rate (a power law and a saturating curve compete on robust residuals; a trophy's own value enters only through a count-based empirical-Bayes weight), then rolls both counts forward as a renewal mixture over the number of refreshes before the target — so when the next refresh is a coin flip, the median sits between the diluted and undiluted rates instead of committing to one of them. With no refresh in the history it falls back to launch-night priors from the brief itself. Growth decay is estimated only when at least five refreshes have been observed. Uncertainty is carried on the logit scale and grows with the number of refreshes ahead and with how small the earner count is. Pure Python standard library, deterministic, offline.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wa8s3t3t&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards</sub>
