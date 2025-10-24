"""
Count trades taken by ORB strategy across all available days using MarketContext filtering.
Print a concise summary of trade frequency and basic breakdown.
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


def main():
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), '..', DATA_FILE_PATH)
    handler = DataHandler(data_path)
    df = handler.load_data()

    # Prepare strategy and context
    strategy = ORBStrategy(stop_buffer_points=ORB_STRATEGY_CONFIG['stop_buffer_points'])
    context_data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    market_context = MarketContext(data_dir=context_data_dir)

    # Build date list from data
    # Use datetime column to ensure proper datetime handling
    all_dates = sorted(df['datetime'].dt.date.unique())

    total_days = 0
    with_orb = 0
    trades_taken = 0
    no_breakout = 0

    for d in all_dates:
        total_days += 1
        date_str = pd.Timestamp(d).strftime('%Y-%m-%d')

        range_high, range_low = strategy.calculate_orb_range(df, date_str)
        if range_high is None or range_low is None:
            continue  # no ORB candle
        with_orb += 1

        analysis = strategy.analyze_single_day(df, date_str, market_context=market_context)
        if analysis['status'] == 'Breakout' and analysis['breakout'] is not None:
            trades_taken += 1
        else:
            no_breakout += 1

    print("=" * 70)
    print("ORB TRADE COUNT WITH MARKET CONTEXT")
    print("=" * 70)
    print(f"Total calendar days: {total_days}")
    print(f"Days with ORB candle: {with_orb}")
    print(f"Trades taken (after context filtering): {trades_taken}")
    if with_orb > 0:
        print(f"Hit rate of taking a trade per ORB day: {trades_taken/with_orb*100:.1f}%")
    print(f"No trade on ORB day (stayed in range or filtered): {no_breakout}")


if __name__ == "__main__":
    main()
