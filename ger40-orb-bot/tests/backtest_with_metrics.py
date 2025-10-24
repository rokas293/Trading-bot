"""
Backtest with Metrics: Compare strict vs soft policies with win rate, profit factor, and fakeout stats.
Uses money management (1% risk per trade) to calculate realistic P&L.
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

# Money Management
ACCOUNT_BALANCE = 10000.0
RISK_PER_TRADE = 0.01
GER40_POINT_VALUE = 1.0


def track_trade_outcome(df, target_date, entry_price, stop_loss, take_profit, signal_type, entry_time):
    """Track whether trade hits TP or SL."""
    target_date = pd.to_datetime(target_date).date()
    date_filter = df['datetime'].dt.date == target_date
    post_entry_data = df[date_filter & (df['datetime'] > entry_time)].copy()
    
    for index, candle in post_entry_data.iterrows():
        if signal_type == 'BUY':
            if candle['high'] >= take_profit:
                return 'TP_HIT', take_profit, candle['datetime']
            elif candle['low'] <= stop_loss:
                return 'SL_HIT', stop_loss, candle['datetime']
        elif signal_type == 'SELL':
            if candle['low'] <= take_profit:
                return 'TP_HIT', take_profit, candle['datetime']
            elif candle['high'] >= stop_loss:
                return 'SL_HIT', stop_loss, candle['datetime']
    
    return 'NO_EXIT', None, None


def backtest_policy(df, mc, policy, enable_fakeouts=False):
    """Run backtest for a given policy and return metrics."""
    strategy = ORBStrategy(stop_buffer_points=ORB_STRATEGY_CONFIG['stop_buffer_points'])
    all_dates = sorted(df['datetime'].dt.date.unique())
    
    balance = ACCOUNT_BALANCE
    trades = []
    
    for d in all_dates:
        date_str = pd.Timestamp(d).strftime('%Y-%m-%d')
        rh, rl = strategy.calculate_orb_range(df, date_str)
        if rh is None or rl is None:
            continue
        
        res = strategy.analyze_single_day(
            df, date_str, market_context=mc,
            context_policy=policy,
            min_1h_strength=30,
            max_orb_pct=0.004,
            max_liq_distance_pct=0.005,
            enable_fakeouts=enable_fakeouts
        )
        
        # Check for breakout or fakeout entry
        entry = res.get('breakout') or res.get('fakeout')
        if entry is None:
            continue
        
        # Money management
        risk_points = entry['risk']
        risk_amount = balance * RISK_PER_TRADE
        position_size = risk_amount / (risk_points * GER40_POINT_VALUE)
        
        # Track outcome
        outcome, exit_price, exit_time = track_trade_outcome(
            df, date_str, entry['entry_price'], entry['stop_loss'],
            entry['take_profit'], entry['signal_type'], entry['breakout_time']
        )
        
        if outcome == 'TP_HIT':
            pnl_points = entry['reward']
            pnl_euro = pnl_points * position_size * GER40_POINT_VALUE
            balance += pnl_euro
            win = True
        elif outcome == 'SL_HIT':
            pnl_points = -entry['risk']
            pnl_euro = pnl_points * position_size * GER40_POINT_VALUE
            balance += pnl_euro
            win = False
        else:
            pnl_points = 0
            pnl_euro = 0
            win = None  # No exit
        
        trades.append({
            'date': date_str,
            'type': entry.get('entry_type', 'breakout'),
            'signal': entry['signal_type'],
            'outcome': outcome,
            'pnl_euro': pnl_euro,
            'win': win
        })
    
    # Calculate metrics
    wins = [t for t in trades if t['win'] is True]
    losses = [t for t in trades if t['win'] is False]
    fakeouts = [t for t in trades if t['type'] == 'fakeout']
    
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    total_pnl = sum(t['pnl_euro'] for t in trades)
    gross_profit = sum(t['pnl_euro'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl_euro'] for t in losses)) if losses else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
    
    return {
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'fakeouts': len(fakeouts),
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'final_balance': balance,
        'profit_factor': profit_factor
    }


def main():
    data_path = os.path.join(os.path.dirname(__file__), '..', DATA_FILE_PATH)
    handler = DataHandler(data_path)
    df = handler.load_data()

    mc = MarketContext(data_dir=os.path.join(os.path.dirname(__file__), '..', 'data'))

    print("="*80)
    print("BACKTEST WITH METRICS: Strict vs Soft vs Soft+Fakeouts")
    print("="*80)
    print(f"Starting Balance: EUR {ACCOUNT_BALANCE:,.2f}")
    print(f"Risk per trade: {RISK_PER_TRADE*100:.1f}%\n")
    
    strict_metrics = backtest_policy(df, mc, 'strict', enable_fakeouts=False)
    soft_metrics = backtest_policy(df, mc, 'soft', enable_fakeouts=False)
    soft_fakeout_metrics = backtest_policy(df, mc, 'soft', enable_fakeouts=True)
    
    def print_metrics(name, m):
        print(f"\n{name}:")
        print(f"  Trades: {m['trades']} (Wins: {m['wins']}, Losses: {m['losses']}, Fakeouts: {m['fakeouts']})")
        print(f"  Win Rate: {m['win_rate']:.1f}%")
        print(f"  Total P&L: EUR {m['total_pnl']:+,.2f}")
        print(f"  Final Balance: EUR {m['final_balance']:,.2f}")
        print(f"  Profit Factor: {m['profit_factor']:.2f}")
    
    print_metrics("STRICT Policy", strict_metrics)
    print_metrics("SOFT Policy", soft_metrics)
    print_metrics("SOFT + Fakeouts", soft_fakeout_metrics)
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
