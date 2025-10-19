"""
Multi-day ORB Strategy Test

Tests the ORB strategy across multiple days to verify:
- Strategy logic works correctly
- Data handling functions properly  
- Integration between components
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

from data_handler import DataHandler
from orb_strategy import ORBStrategy
from settings import ORB_STRATEGY_CONFIG, DATA_FILE_PATH

# Money Management Configuration
ACCOUNT_BALANCE = 10000.0  # Starting account balance in EUR
RISK_PER_TRADE = 0.01      # 1% risk per trade
GER40_POINT_VALUE = 1.0    # 1 EUR per point for GER40 CFD

def calculate_position_size(account_balance, risk_per_trade, risk_points, point_value):
    """Calculate position size based on 1% risk management"""
    risk_amount = account_balance * risk_per_trade  # Amount willing to lose
    position_size = risk_amount / (risk_points * point_value)  # Position size
    return position_size, risk_amount

def track_trade_outcome(df, target_date, entry_price, stop_loss, take_profit, signal_type, entry_time, position_size, account_balance):
    """Track what happens to the trade after entry - does it hit TP or SL?"""
    target_date = pd.to_datetime(target_date).date()
    date_filter = df['datetime'].dt.date == target_date
    
    # Get candles after entry time
    post_entry_data = df[date_filter & (df['datetime'] > entry_time)].copy()
    
    for index, candle in post_entry_data.iterrows():
        if signal_type == 'BUY':
            # Check if TP hit first (price goes up to target)
            if candle['high'] >= take_profit:
                points_profit = take_profit - entry_price
                euro_profit = points_profit * position_size * GER40_POINT_VALUE
                new_balance = account_balance + euro_profit
                return {
                    'outcome': 'TP_HIT',
                    'exit_price': take_profit,
                    'exit_time': candle['datetime'],
                    'profit_loss_points': points_profit,
                    'profit_loss_euro': euro_profit,
                    'new_balance': new_balance,
                    'rr_achieved': (take_profit - entry_price) / (entry_price - stop_loss)
                }
            # Check if SL hit (price goes down to stop)
            elif candle['low'] <= stop_loss:
                points_loss = stop_loss - entry_price
                euro_loss = points_loss * position_size * GER40_POINT_VALUE
                new_balance = account_balance + euro_loss  # euro_loss is negative
                return {
                    'outcome': 'SL_HIT',
                    'exit_price': stop_loss,
                    'exit_time': candle['datetime'],
                    'profit_loss_points': points_loss,
                    'profit_loss_euro': euro_loss,
                    'new_balance': new_balance,
                    'rr_achieved': (stop_loss - entry_price) / (entry_price - stop_loss)
                }
        
        elif signal_type == 'SELL':
            # Check if TP hit first (price goes down to target)
            if candle['low'] <= take_profit:
                points_profit = entry_price - take_profit
                euro_profit = points_profit * position_size * GER40_POINT_VALUE
                new_balance = account_balance + euro_profit
                return {
                    'outcome': 'TP_HIT',
                    'exit_price': take_profit,
                    'exit_time': candle['datetime'],
                    'profit_loss_points': points_profit,
                    'profit_loss_euro': euro_profit,
                    'new_balance': new_balance,
                    'rr_achieved': (entry_price - take_profit) / (stop_loss - entry_price)
                }
            # Check if SL hit (price goes up to stop)
            elif candle['high'] >= stop_loss:
                points_loss = entry_price - stop_loss
                euro_loss = points_loss * position_size * GER40_POINT_VALUE
                new_balance = account_balance + euro_loss  # euro_loss is negative
                return {
                    'outcome': 'SL_HIT',
                    'exit_price': stop_loss,
                    'exit_time': candle['datetime'],
                    'profit_loss_points': points_loss,
                    'profit_loss_euro': euro_loss,
                    'new_balance': new_balance,
                    'rr_achieved': (entry_price - stop_loss) / (stop_loss - entry_price)
                }
    
    # If we get here, neither TP nor SL was hit by end of day
    return {
        'outcome': 'NO_EXIT',
        'exit_price': None,
        'exit_time': None,
        'profit_loss_points': 0,
        'profit_loss_euro': 0,
        'new_balance': account_balance,
        'rr_achieved': 0
    }

def analyze_day_with_money_management(strategy, df, date, account_balance):
    """Enhanced day analysis with trade outcome tracking and money management"""
    import pandas as pd
    
    # Get ORB range
    range_high, range_low = strategy.calculate_orb_range(df, date)
    
    if range_high is None or range_low is None:
        return {
            'date': date,
            'status': 'No ORB candle',
            'balance_before': account_balance,
            'balance_after': account_balance
        }
    
    range_size = range_high - range_low
    
    # Check for breakouts with enhanced tracking
    breakout = strategy.detect_orb_breakout(df, date, range_high, range_low)
    
    if breakout:
        # Calculate position size based on 1% risk
        risk_points = breakout['risk']
        position_size, risk_amount_euro = calculate_position_size(
            account_balance, RISK_PER_TRADE, risk_points, GER40_POINT_VALUE
        )
        
        # Track what happens to this trade
        trade_outcome = track_trade_outcome(
            df, date, breakout['entry_price'], breakout['stop_loss'], 
            breakout['take_profit'], breakout['signal_type'], 
            breakout['breakout_time'], position_size, account_balance
        )
        
        return {
            'date': date,
            'status': 'Breakout',
            'signal_type': breakout['signal_type'],
            'entry_price': breakout['entry_price'],
            'stop_loss': breakout['stop_loss'],
            'take_profit': breakout['take_profit'],
            'risk_points': risk_points,
            'risk_amount_euro': risk_amount_euro,
            'position_size': position_size,
            'range_size': range_size,
            'breakout_time': breakout['breakout_time'],
            'outcome': trade_outcome['outcome'],
            'exit_price': trade_outcome['exit_price'],
            'exit_time': trade_outcome['exit_time'],
            'profit_loss_points': trade_outcome['profit_loss_points'],
            'profit_loss_euro': trade_outcome['profit_loss_euro'],
            'balance_before': account_balance,
            'balance_after': trade_outcome['new_balance'],
            'actual_rr': trade_outcome['rr_achieved']
        }
    else:
        return {
            'date': date,
            'status': 'No breakout',
            'range_size': range_size,
            'balance_before': account_balance,
            'balance_after': account_balance
        }

def main():
    print("="*70)
    print("ENHANCED ORB STRATEGY TEST WITH MONEY MANAGEMENT")
    print("="*70)
    
    # Initialize components
    print("🚀 Initializing components...")
    
    # Data handler
    data_path = os.path.join(os.path.dirname(__file__), '..', DATA_FILE_PATH)
    handler = DataHandler(data_path)
    
    try:
        df = handler.load_data()
        handler.print_data_summary()
        
        # Validate data integrity
        if not handler.validate_data_integrity():
            print("❌ Data validation failed!")
            return
            
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Strategy
    strategy = ORBStrategy(stop_buffer_points=ORB_STRATEGY_CONFIG['stop_buffer_points'])
    print(f"\n📊 Strategy Configuration:")
    strategy_summary = strategy.get_strategy_summary()
    for key, value in strategy_summary.items():
        print(f"  {key}: {value}")
    
    # Money Management Setup
    print(f"\n💰 Money Management:")
    print(f"  Starting Balance: EUR {ACCOUNT_BALANCE:,.2f}")
    print(f"  Risk per Trade: {RISK_PER_TRADE*100:.1f}%")
    print(f"  Point Value: EUR {GER40_POINT_VALUE} per point")
    
    # Test dates - use dates we know exist in our 7-day sample
    test_dates = [
        '2025-09-18',
        '2025-09-19', 
        '2025-09-22',
        '2025-09-23',
        '2025-09-24'
    ]
    
    print(f"\n🧪 Testing {len(test_dates)} days with trade tracking...")
    results = []
    current_balance = ACCOUNT_BALANCE
    
    for date in test_dates:
        print(f"\n{'='*50}")
        print(f"📅 Testing: {date}")
        print(f"Current Balance: EUR {current_balance:,.2f}")
        print(f"{'='*50}")
        
        # Analyze single day with money management
        analysis = analyze_day_with_money_management(strategy, df, date, current_balance)
        
        if analysis['status'] == 'No ORB candle':
            print(f"❌ No ORB candle found for {date}")
        elif analysis['status'] == 'No breakout':
            print(f"📊 ORB Range: {analysis['range_size']:.1f} points")
            print(f"📈 No breakout - stayed in range")
        elif analysis['status'] == 'Breakout':
            print(f"📊 ORB Range: {analysis['range_size']:.1f} points")
            print(f"🚨 {analysis['signal_type']} SIGNAL!")
            print(f"   Entry: {analysis['entry_price']:.1f}")
            print(f"   Stop:  {analysis['stop_loss']:.1f}")
            print(f"   Target: {analysis['take_profit']:.1f}")
            print(f"   Risk: {analysis['risk_points']:.1f} points (EUR {analysis['risk_amount_euro']:.2f})")
            print(f"   Position Size: {analysis['position_size']:.2f} units")
            print(f"   Time: {analysis['breakout_time'].strftime('%H:%M')} UTC")
            
            # Show trade outcome
            if analysis['outcome'] == 'TP_HIT':
                print(f"   ✅ TARGET HIT at {analysis['exit_price']:.1f}")
                print(f"   Profit: +{analysis['profit_loss_points']:.1f} points (EUR +{analysis['profit_loss_euro']:.2f})")
                print(f"   Actual R:R: {analysis['actual_rr']:.2f}:1")
            elif analysis['outcome'] == 'SL_HIT':
                print(f"   ❌ STOP LOSS HIT at {analysis['exit_price']:.1f}")
                print(f"   Loss: {analysis['profit_loss_points']:.1f} points (EUR {analysis['profit_loss_euro']:.2f})")
                print(f"   Actual R:R: {analysis['actual_rr']:.2f}:1")
            else:
                print(f"   ⏸️ NO EXIT (neither TP nor SL hit)")
            
            # Update running balance
            current_balance = analysis['balance_after']
            print(f"   New Balance: EUR {current_balance:,.2f}")
        
        results.append(analysis)
    
    # Enhanced Summary with Win Rate and P&L
    print(f"\n{'='*70}")
    print("💰 COMPREHENSIVE STRATEGY PERFORMANCE")
    print(f"{'='*70}")
    
    total_tests = len(results)
    breakout_count = sum(1 for r in results if r['status'] == 'Breakout')
    no_breakout_count = sum(1 for r in results if r['status'] == 'No breakout')
    no_orb_count = sum(1 for r in results if r['status'] == 'No ORB candle')
    
    # Trade outcome statistics
    winning_trades = sum(1 for r in results if r.get('outcome') == 'TP_HIT')
    losing_trades = sum(1 for r in results if r.get('outcome') == 'SL_HIT')
    no_exit_trades = sum(1 for r in results if r.get('outcome') == 'NO_EXIT')
    
    buy_signals = sum(1 for r in results if r.get('signal_type') == 'BUY')
    sell_signals = sum(1 for r in results if r.get('signal_type') == 'SELL')
    
    print(f"💰 ACCOUNT PERFORMANCE:")
    print(f"Starting Balance: EUR {ACCOUNT_BALANCE:,.2f}")
    print(f"Final Balance: EUR {current_balance:,.2f}")
    print(f"Total Return: EUR {current_balance - ACCOUNT_BALANCE:+,.2f}")
    print(f"Return Percentage: {((current_balance - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100:+.2f}%")
    
    print(f"\n📊 BASIC STATISTICS:")
    print(f"Total days tested: {total_tests}")
    print(f"Days with ORB candle: {total_tests - no_orb_count}")
    print(f"Days with breakouts: {breakout_count}")
    print(f"Days without breakouts: {no_breakout_count}")
    print(f"Days missing ORB candle: {no_orb_count}")
    
    print(f"\n📈 SIGNAL BREAKDOWN:")
    print(f"BUY signals: {buy_signals}")
    print(f"SELL signals: {sell_signals}")
    
    print(f"\n🎯 TRADE OUTCOMES:")
    print(f"Winning trades (TP hit): {winning_trades}")
    print(f"Losing trades (SL hit): {losing_trades}")
    print(f"No exit trades: {no_exit_trades}")
    
    if breakout_count > 0:
        win_rate = (winning_trades / breakout_count) * 100
        print(f"\n🏆 WIN RATE: {win_rate:.1f}%")
        
        # P&L Statistics in both points and EUR
        total_pnl_points = sum(r.get('profit_loss_points', 0) for r in results if r.get('profit_loss_points') is not None)
        total_pnl_euro = sum(r.get('profit_loss_euro', 0) for r in results if r.get('profit_loss_euro') is not None)
        
        if winning_trades > 0:
            avg_winner_points = sum(r['profit_loss_points'] for r in results if r.get('outcome') == 'TP_HIT') / winning_trades
            avg_winner_euro = sum(r['profit_loss_euro'] for r in results if r.get('outcome') == 'TP_HIT') / winning_trades
        else:
            avg_winner_points = avg_winner_euro = 0
            
        if losing_trades > 0:
            avg_loser_points = sum(r['profit_loss_points'] for r in results if r.get('outcome') == 'SL_HIT') / losing_trades
            avg_loser_euro = sum(r['profit_loss_euro'] for r in results if r.get('outcome') == 'SL_HIT') / losing_trades
        else:
            avg_loser_points = avg_loser_euro = 0
        
        print(f"\n💵 PROFIT & LOSS:")
        print(f"Total P&L: {total_pnl_points:+.1f} points (EUR {total_pnl_euro:+,.2f})")
        print(f"Average winner: +{avg_winner_points:.1f} points (EUR +{avg_winner_euro:,.2f})" if winning_trades > 0 else "Average winner: N/A")
        print(f"Average loser: {avg_loser_points:.1f} points (EUR {avg_loser_euro:,.2f})" if losing_trades > 0 else "Average loser: N/A")
    
    # Detailed results table
    print(f"\n{'='*80}")
    print("📋 DETAILED TRADE RESULTS")
    print(f"{'='*80}")
    for r in results:
        if r['status'] == 'Breakout':
            outcome_symbol = "🏆 WIN" if r['outcome'] == 'TP_HIT' else "💥 LOSS" if r['outcome'] == 'SL_HIT' else "⏸️ NO_EXIT"
            print(f"{r['date']}: {r['signal_type']} @ {r['entry_price']:.1f}")
            print(f"   Risk: {r['risk_points']:.1f}pts (EUR {r['risk_amount_euro']:.2f}) | Size: {r['position_size']:.2f} units")
            print(f"   {outcome_symbol} | P&L: {r['profit_loss_points']:+.1f}pts (EUR {r['profit_loss_euro']:+.2f})")
            print(f"   Balance: EUR {r['balance_before']:,.2f} -> EUR {r['balance_after']:,.2f}")
        else:
            print(f"{r['date']}: {r['status']}")
    
    print(f"\n{'='*80}")
    print(f"🎯 FINAL SUMMARY: Started with EUR {ACCOUNT_BALANCE:,.2f}, ended with EUR {current_balance:,.2f}")
    print(f"💰 NET RESULT: EUR {current_balance - ACCOUNT_BALANCE:+,.2f} ({((current_balance - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100:+.2f}%)")
    print(f"{'='*80}")

    if breakout_count > 0:
        print(f"✅ Strategy is working: {breakout_count} breakouts with {winning_trades} wins, {losing_trades} losses")
    else:
        print("📈 No breakouts in test period - strategy ready for different market conditions")

if __name__ == "__main__":
    main()