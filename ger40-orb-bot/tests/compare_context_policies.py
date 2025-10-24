"""
Compare trade frequency between STRICT and SOFT context policies over all available days.
Outputs counts and basic percentages to help choose tuning goals.
"""
import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

from data_handler import DataHandler
from orb_strategy import ORBStrategy
from market_context import MarketContext
from settings import ORB_STRATEGY_CONFIG, DATA_FILE_PATH


def count_trades(df: pd.DataFrame, mc: MarketContext, policy: str) -> dict:
    strategy = ORBStrategy(stop_buffer_points=ORB_STRATEGY_CONFIG['stop_buffer_points'])
    all_dates = sorted(df['datetime'].dt.date.unique())

    with_orb = 0
    taken = 0

    for d in all_dates:
        date_str = pd.Timestamp(d).strftime('%Y-%m-%d')
        rh, rl = strategy.calculate_orb_range(df, date_str)
        if rh is None or rl is None:
            continue
        with_orb += 1
        res = strategy.analyze_single_day(
            df, date_str, market_context=mc,
            context_policy=policy,
            min_1h_strength=30,
            max_orb_pct=0.004,
            max_liq_distance_pct=0.005
        )
        if res['status'] == 'Breakout' and res['breakout'] is not None:
            taken += 1

    return {
        'with_orb': with_orb,
        'taken': taken,
        'rate': (taken/with_orb*100 if with_orb else 0.0)
    }


def main():
    data_path = os.path.join(os.path.dirname(__file__), '..', DATA_FILE_PATH)
    handler = DataHandler(data_path)
    df = handler.load_data()

    mc = MarketContext(data_dir=os.path.join(os.path.dirname(__file__), '..', 'data'))

    strict_stats = count_trades(df, mc, 'strict')
    soft_stats = count_trades(df, mc, 'soft')

    print("="*72)
    print("STRICT vs SOFT Context Policies — Trade Frequency Comparison")
    print("="*72)
    print(f"Days with ORB candle: {strict_stats['with_orb']}")
    print(f"STRICT: trades taken = {strict_stats['taken']} ({strict_stats['rate']:.1f}% of ORB days)")
    print(f"SOFT:   trades taken = {soft_stats['taken']} ({soft_stats['rate']:.1f}% of ORB days)")


if __name__ == "__main__":
    main()
