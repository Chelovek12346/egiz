# ML Stage 2 results: pre-registered evaluation on documented analog sites

Written with AI assistance (Claude Code); human review pending. 15 November 2026.

- Pre-registration: `docs/ML_PREREGISTRATION.md`, frozen in commit 1b5fa62. `data/ml/reference/FREEZE.json` was written at 2026-11-15T03:47Z, before any reference AOI was scored.
- Run: `python -m pipeline.ml evaluate`, the first and only run.
- Output: `data/ml/results/stage2-evaluation-0.1.0.json`, which embeds the freeze record.

## Verdicts (decision rule §5, applied as written)

| Analysis | Pairs (sites) | Median pct | 95 % CI of median (site bootstrap) | hit@10 % | Dryness-only median | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **P1 (primary)** | 14 (13) | **14.6 %** | 8.5 – 50.0 % | 4 / 14 (binomial p = 0.044) | 58.4 % | **inconclusive** |
| S1 (+ grade C, + area) | 25 (24) | 12.5 % | 7.1 – 46.0 % | 9 / 25 (p = 0.0005) | 54.2 % | inconclusive |
| S2 (target-free attributes) | 13 (13) | 43.6 % | 34.5 – 44.6 % | 0 / 13 | 58.4 % | not_confirmed |
| S4 (P1 without Apollo-era) | 3 (2) | 22.9 % | 19.6 – 50.9 % | 0 / 3 | 29.7 % | inconclusive (< 8 pairs) |

Random ordering: the P1 median of 14.6 % is lower than random in 99.96 % of 10 000 simulations (p = 0.0004).

## What this means

1. **The point estimate meets the success criterion, but the uncertainty is too large to call it.** The median documented training site sits in the top 15 % of 296 Earth AOIs for its task. That is far better than dryness-only (58 %) and than random (50 %). The upper end of the site-clustered interval reaches 50 %, though, so by the pre-registered rule the result is `inconclusive`, not `confirmed`. With 13 sites, a few far-down sites (Ries 80 %, Capulin 67 %, Kilbourne Hole 50 %, SP Crater 51 %) widen the interval a lot.
2. **The target comparison does the work.** S2 drops the comparison with Mons Mouton and keeps only "bare surface ≥ 70 %". It falls to a 44 % median and `not_confirmed`. Exposed ground alone does not find these sites; matching the target's relief and traversable-slope share does.
3. **The result is about O2 only.** In practice P1 tests "EVA and field geology" against Apollo-era volcanic and impact training fields. It says nothing about landing (O1, M1), low-Sun operations (O4) or cold and dry (O5, M4).
4. **Absolute F values are low** (0.002 – 0.19 for the reference sites). The O2 terrain of Mons Mouton is matched poorly by any Earth window, and the ranking works on small differences. This is a property of the target and the σ values, not a bug, but it should be stated whenever F is shown.

## Per pair (P1)

| Site | Task | pct | F | Top 10 % in stability draws |
| --- | --- | --- | --- | --- |
| Ubehebe Crater | O2 | 2.7 % | 0.186 | 100 % |
| Kilauea / Kilauea Iki | O2 | 6.8 % | 0.056 | 89 % |
| Valley of Ten Thousand Smokes | O2 | 7.1 % | 0.045 | 80 % |
| Askja caldera | O2 | 8.4 % | 0.038 | 62 % |
| Medicine Lake Volcano | O2 | 11.1 % | 0.020 | 7 % |
| Newberry Volcano | O2 | 12.5 % | 0.013 | 0 % |
| Sunset Crater | O2 | 12.9 % | 0.011 | 0 % |
| Haughton crater | O3 | 16.2 % | 0.036 | 1 % |
| Haughton crater | M2 | 22.9 % | 0.277 | 1 % |
| Meteor Crater | O2 | 45.9 % | 0.006 | 0 % |
| Kilbourne Hole | O2 | 50.0 % | 0.004 | 0 % |
| SP Crater (JETT3) | O2 | 50.8 % | 0.004 | 0 % |
| Capulin Volcano | O2 | 67.2 % | 0.002 | 0 % |
| Nördlinger Ries | O2 | 80.1 % | 0.002 | 0 % |

Pattern, not tested (observed after the run): volcanic fields rank high. Impact craters and isolated small features rank low: Ries (24 km crater, now farmland), Meteor Crater (1.2 km, a small feature inside a 22 km window), Kilbourne Hole (maar), Capulin (a single cone). A 22 km window dilutes small features. This is a hypothesis for the next version, not a result.

## What would make the next evaluation decisive

- **More sites per task, beyond Apollo-era O2.** Coordinates for Black Point Lava Flow (D-RATS, JETT) and Sierra Blanca; the JETT 1–5 locations; landing and low-Sun rehearsal sites.
- Any change of window size or rules must be a dated amendment, and it must be evaluated on **new** sites, not on these 14. Otherwise it is fitted to this result.
