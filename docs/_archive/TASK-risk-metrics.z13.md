> ARCHIVED 2026-06-19 — frozen historical snapshot; current status lives in [/ROADMAP.md](../../ROADMAP.md). This task brief is preserved for provenance; the work it describes shipped on `master` @ `ed6a1f1`.

# TASK: phantom-quant — risk-adjusted performance metrics (Sharpe + CAGR + annualized volatility) in report.metrics()

Repo: D:\Projects\phantom-quant (z13). Python. Default branch: master. Branch: sat/quant-risk-metrics (off origin/master). Scouted @ac537ff.

## YOU ORCHESTRATE ONLY — do NOT write the code yourself. Minimize your own tokens.
- Code: `D:\Projects\phantom-mesh-private\.claude\skills\local-ai\ask.sh codex "implement <one fn/edit + a failing test>"` (one file/call, lint after).
- Reading: `... ask.sh opencode "read phantom_quant/report.py metrics() + how the equity curve is built + the run.json/report.md artifact writers"`. 2nd-op: `... ask.sh agy "<q>"`.
- Run tests yourself; gate via `ask.sh all`; commit. Write code yourself ONLY if codex flakes twice.

## The gap (scout-verified on origin/master @ac537ff)
phantom_quant/report.py `metrics()` computes ONLY total_return, max_drawdown, num_trades/num_closed, ending_cash, realized_pnl,
total_costs, num_gated/num_rejected, wins/losses — there is NO risk-adjusted or annualized metric (`git grep -niE
"sharpe|sortino|cagr|annual|volatilit|stdev|risk.?free|calmar"` = ZERO in product/tests). For a backtest engine whose pitch is
"honest numbers, every number re-derivable from the equity curve" (README), the absence of Sharpe (the single most-cited quant metric)
is a genuine vision gap. Add the risk-adjusted metrics, ALL derived from the existing equity curve.

## VERIFY-FIRST then implement
1. `git fetch origin`; `git switch -c sat/quant-risk-metrics origin/master`.
2. `ask.sh opencode "show phantom_quant/report.py metrics() (its exact return dict + what equity-curve/series it has access to:
   per-bar equity values + their dates/timestamps?), and where metrics() flows into run.json + report.md artifacts."` Read yourself +
   confirm the equity series + its time index are available (Sharpe/CAGR need periodic returns + a span).
3. HONEST-BAIL if Sharpe/CAGR already exist.

## Goal (genuine, surfaced in the real artifacts, derived from the equity curve)
- Add to metrics(): `sharpe` (annualized: mean(periodic_return)/stdev(periodic_return) * sqrt(periods_per_year), risk_free default 0,
  documented), `cagr` (annualized return from first→last equity over the elapsed years), `annualized_volatility` (stdev(periodic_return)
  * sqrt(periods_per_year)). Infer periods_per_year from the bar cadence (daily≈252) or take it as a documented param/default. Pure
  stdlib math (statistics.mean/pstdev) — NO numpy/scipy if the project is stdlib. Handle <2 returns / zero-variance gracefully (None/0, documented).
- These flow into the existing run.json + report.md artifacts automatically (metrics() feeds them) — confirm they appear.

## MANDATORY anti-fake-green VERIFICATION (real numbers, re-derivable from the equity curve)
A test that: (1) runs a real backtest (or feeds a known equity curve) and asserts metrics()["sharpe"]/["cagr"]/["annualized_volatility"]
equal HAND-COMPUTED values for that curve (compute the expected Sharpe/CAGR by hand in the test from the same returns — proves it's the
real formula, not a stub); (2) asserts the metrics appear in the emitted run.json AND report.md (the real artifacts); (3) an edge case
(flat equity → vol 0 → Sharpe None/0 documented; single bar → graceful). This must reflect the REAL equity curve (re-derivable), per the README pitch.

## HARD RULES (gate WILL reject — anti-fake-green)
- The metrics are REAL (formula correct, matching hand-computed values) + appear in the real run.json/report.md artifacts. Reject if
  they're hard-coded, wrong, or not surfaced.
- ADDITIVE: never delete tests or revert fixes; keep ALL existing tests green (113+); lint clean. Derive from the existing equity curve —
  do NOT change the engine/backtest. HONEST-BAIL: if the bar cadence/periods-per-year can't be inferred, take it as a documented param default (don't fake).

## Self-gate (trio) — need >=2 distinct-AI LGTM
`D:\Projects\phantom-mesh-private\.claude\skills\local-ai\ask.sh all "Review sat/quant-risk-metrics via 'git diff origin/master..HEAD'. Confirm (1) metrics() now computes sharpe + cagr + annualized_volatility from the EXISTING equity curve (correct annualized formulas, stdlib statistics, risk_free/periods documented, graceful on <2 returns / zero variance); (2) a test asserts these equal HAND-COMPUTED values for a known curve (real formula, not a stub) AND that they appear in the emitted run.json + report.md artifacts; (3) ADDITIVE, no deleted tests (--diff-filter=D), all 113+ prior green, lint clean, engine/backtest unchanged. ANTI-FAKE-GREEN: reject if the metrics are hard-coded/wrong or not surfaced in the real artifacts. Verdict LGTM or FIX_FIRST."`

## Finish
`git push -u origin sat/quant-risk-metrics` (push only, do NOT merge). Print: the new metrics + formulas, the test output (hand-computed match + artifact presence), gate verdicts.

Commits must end with:

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
