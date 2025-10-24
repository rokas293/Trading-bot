# Context Policies: Strict vs Soft

This document explains how the ORB strategy uses market context to gate trades, what changed, and how to reproduce comparison results.

## What changed

- `orb_strategy.analyze_single_day(...)` now accepts a context policy and thresholds:
  - `context_policy`: `'strict'` or `'soft'`
  - `min_1h_strength`: default 30 (1H trend strength threshold)
  - `max_orb_pct`: default 0.004 (0.4% of price)
  - `max_liq_distance_pct`: default 0.005 (0.5% of price)
- Strict policy (previous behavior):
  - BUY allowed only when context alignment ∈ {`bullish`, `weak_bullish`}
  - SELL allowed only when context alignment ∈ {`bearish`, `weak_bearish`}
- Soft policy (new):
  - Opposite alignment (e.g., `weak_bearish` vs BUY) is blocked unless BOTH:
    - 1H trend supports the trade and strength ≥ `min_1h_strength`, AND
    - There is nearby liquidity beyond the breakout side within `max_liq_distance_pct`.
  - `mixed` alignment is allowed if ANY of:
    - 1H supports with strength ≥ `min_1h_strength`, OR
    - Nearby liquidity beyond breakout side within `max_liq_distance_pct`, OR
    - ORB range size ≤ `max_orb_pct` of price.

Liquidity comes from `MarketContext.detect_liquidity_pools()`, which returns recent swing highs/lows and equal highs/lows on the Daily timeframe.

## Why

- Goal: increase daily participation without destroying win quality.
- Strategy: keep strong alignment as green-light; allow `mixed` when you have additional microstructure or volatility signals (1H strength, liquidity incentive, small range). Block outright conflict unless confirmation is strong.

## How to run comparisons

- Trade count with current strict policy:
  - `tests/trade_count_with_context.py` (reports how many trades are taken after context filtering)
- Strict vs Soft comparison:
  - `tests/compare_context_policies.py`
  - Output example from current dataset:
    - Days with ORB candle: 238
    - STRICT: trades taken = 113 (47.5% of ORB days)
    - SOFT: trades taken = 188 (79.0% of ORB days)

## Tuning knobs

- `min_1h_strength` (default 30): raise to reduce `mixed` approvals; lower to increase.
- `max_orb_pct` (default 0.4%): smaller ranges are easier to break; lower threshold reduces approvals.
- `max_liq_distance_pct` (default 0.5%): larger threshold considers more liquidity levels as “nearby”; lower reduces approvals.

## Notes for write-up

- Contract for gating:
  - Inputs: context alignment, 1H trend (dir+strength), liquidity pools, ORB range.
  - Output: allow/block trade (+ reason code in results: `gate_reason`).
  - Error modes: missing context → skip gating (falls back to previous behavior), sparse liquidity lists → condition may not trigger.
- Edge cases considered:
  - Very large ORB range days → blocked unless strong context.
  - Conflicting alignment vs microstructure → require stronger confirmation.
  - Timezone consistency: all context dates are UTC-aware.

## Next steps

- Add fakeout setup (trade re-entry when first break fails) as a complementary entry to increase participation on choppy days.
- Grid-search thresholds to target 85–95% daily participation with acceptable win metrics.
