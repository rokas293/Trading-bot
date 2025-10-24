"""
ORB Strategy Module for GER40 Trading Bot

This module contains the core Opening Range Breakout strategy implementation.
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime

# Import MarketContext for context filtering
from market_context import MarketContext


class ORBStrategy:
    """Opening Range Breakout strategy implementation."""
    
    def __init__(self, stop_buffer_points: float = 5.0):
        """
        Initialize the ORB strategy.
        
        Args:
            stop_buffer_points: Points to place stop loss away from candle open
        """
        self.stop_buffer_points = stop_buffer_points
        
    def get_orb_period_data(self, df: pd.DataFrame, target_date: str) -> pd.DataFrame:
        """
        Find the 8:00-8:15 London ORB candles for a specific date.
        
        Args:
            df: DataFrame with OHLC data
            target_date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            DataFrame containing both ORB candles (8:00 and 8:15 London) for the target date
        """
        # Convert target_date string to datetime.date object for comparison
        target_date_obj = pd.to_datetime(target_date).date()
        
        # Filter conditions:
        # 1. Target date
        date_filter = df['datetime'].dt.date == target_date_obj
        
        # 2. Hour 7 UTC = 8:00-8:59 London time
        hour_filter = df['hour'] == 7
        
        # 3. Minutes 0 and 15 (the 8:00 and 8:15 candles)
        minute_filter = df['datetime'].dt.minute.isin([0, 15])
        
        # Combine all filters to get both ORB candles
        orb_candles = df[date_filter & hour_filter & minute_filter]
        
        return orb_candles
    
    def calculate_orb_range(self, df: pd.DataFrame, target_date: str) -> tuple[Optional[float], Optional[float]]:
        """
        Calculate the ORB range (high and low) for a specific date.
        Uses only the 8:00 London (7:00 UTC) candle for the range.
        
        Args:
            df: DataFrame with OHLC data
            target_date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Tuple of (range_high, range_low) or (None, None) if no ORB candle found
        """
        orb_data = self.get_orb_period_data(df, target_date)
        
        if len(orb_data) == 0:
            return None, None
        
        # Get only the 8:00 London candle (7:00 UTC, minute 0)
        orb_candle = orb_data[orb_data['datetime'].dt.minute == 0]
        
        if len(orb_candle) == 0:
            return None, None
            
        # Use only the 8:00 candle's high and low
        range_high = orb_candle['high'].iloc[0]
        range_low = orb_candle['low'].iloc[0]
        
        return range_high, range_low
    
    def detect_orb_breakout(self, df: pd.DataFrame, target_date: str, 
                           range_high: float, range_low: float) -> Optional[Dict[str, Any]]:
        """
        Detect ORB breakouts after 8:15 London time (07:15 UTC).
        
        Args:
            df: DataFrame with OHLC data
            target_date: Date string in format 'YYYY-MM-DD'
            range_high: The ORB range high level
            range_low: The ORB range low level
            
        Returns:
            Dictionary with breakout information or None if no breakout
        """
        # Convert target_date string to datetime.date object
        target_date_obj = pd.to_datetime(target_date).date()
        
        # Filter for the target date and after 07:15 UTC (8:15 London)
        date_filter = df['datetime'].dt.date == target_date_obj
        
        # After 07:15 UTC means hour > 7 OR (hour == 7 AND minute > 15)
        time_filter = (df['hour'] > 7) | ((df['hour'] == 7) & (df['datetime'].dt.minute > 15))
        
        # Get data after ORB period
        post_orb_data = df[date_filter & time_filter].copy()
        
        # Check each candle for breakouts (close-based for reliability)
        for index, candle in post_orb_data.iterrows():
            # Check for BUY breakout (candle CLOSES above range high)
            if candle['close'] > range_high:
                entry_price = candle['close']  # Enter where candle closes
                
                # Stop loss: buffer points below the entry candle's LOW
                stop_loss = candle['low'] - self.stop_buffer_points
                
                # Calculate risk and set 1:1 reward
                risk = entry_price - stop_loss  # Variable risk based on candle structure
                take_profit = entry_price + risk
                
                return {
                    'signal_type': 'BUY',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk': risk,
                    'reward': risk,  # 1:1 risk/reward
                    'range_high': range_high,
                    'range_low': range_low,
                    'range_size': range_high - range_low,
                    'breakout_time': candle['datetime'],
                    'candle_open': candle['open'],
                    'candle_high': candle['high'],
                    'candle_close': candle['close']
                }
            
            # Check for SELL breakout (candle CLOSES below range low)
            elif candle['close'] < range_low:
                entry_price = candle['close']  # Enter where candle closes
                
                # Stop loss: buffer points above the entry candle's HIGH  
                stop_loss = candle['high'] + self.stop_buffer_points
                
                # Calculate risk and set 1:1 reward
                risk = stop_loss - entry_price  # Variable risk based on candle structure
                take_profit = entry_price - risk
                
                return {
                    'signal_type': 'SELL',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk': risk,
                    'reward': risk,  # 1:1 risk/reward
                    'range_high': range_high,
                    'range_low': range_low,
                    'range_size': range_high - range_low,
                    'breakout_time': candle['datetime'],
                    'candle_open': candle['open'],
                    'candle_low': candle['low'],
                    'candle_close': candle['close']
                }
        
        # No breakout found
        return None

    def detect_fakeout(self, df: pd.DataFrame, target_date: str,
                       range_high: float, range_low: float) -> Optional[Dict[str, Any]]:
        """
        Detect fakeout: price breaks ORB range but closes back inside (failed breakout).
        
        Args:
            df: DataFrame with OHLC data
            target_date: Date string in format 'YYYY-MM-DD'
            range_high: The ORB range high level
            range_low: The ORB range low level
            
        Returns:
            Dictionary with fakeout entry (opposite direction) or None
        """
        target_date_obj = pd.to_datetime(target_date).date()
        date_filter = df['datetime'].dt.date == target_date_obj
        time_filter = (df['hour'] > 7) | ((df['hour'] == 7) & (df['datetime'].dt.minute > 15))
        post_orb_data = df[date_filter & time_filter].copy()

        for index, candle in post_orb_data.iterrows():
            # Check for failed BUY breakout (wick above range_high, but close back inside)
            if candle['high'] > range_high and candle['close'] <= range_high:
                # Fakeout: enter SELL (opposite of failed break)
                entry_price = candle['close']
                stop_loss = candle['high'] + self.stop_buffer_points
                risk = stop_loss - entry_price
                take_profit = entry_price - risk

                return {
                    'signal_type': 'SELL',
                    'entry_type': 'fakeout',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk': risk,
                    'reward': risk,
                    'range_high': range_high,
                    'range_low': range_low,
                    'range_size': range_high - range_low,
                    'breakout_time': candle['datetime'],
                    'candle_open': candle['open'],
                    'candle_high': candle['high'],
                    'candle_close': candle['close'],
                    'fakeout_level': range_high
                }

            # Check for failed SELL breakout (wick below range_low, but close back inside)
            elif candle['low'] < range_low and candle['close'] >= range_low:
                # Fakeout: enter BUY (opposite of failed break)
                entry_price = candle['close']
                stop_loss = candle['low'] - self.stop_buffer_points
                risk = entry_price - stop_loss
                take_profit = entry_price + risk

                return {
                    'signal_type': 'BUY',
                    'entry_type': 'fakeout',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk': risk,
                    'reward': risk,
                    'range_high': range_high,
                    'range_low': range_low,
                    'range_size': range_high - range_low,
                    'breakout_time': candle['datetime'],
                    'candle_open': candle['open'],
                    'candle_low': candle['low'],
                    'candle_close': candle['close'],
                    'fakeout_level': range_low
                }

        return None
    
    def analyze_single_day(
        self,
        df: pd.DataFrame,
        target_date: str,
        market_context: Optional[MarketContext] = None,
        *,
        context_policy: str = 'strict',
        min_1h_strength: int = 30,
        max_orb_pct: float = 0.004,  # 0.4%
        max_liq_distance_pct: float = 0.005,  # 0.5%
        enable_fakeouts: bool = False
    ) -> Dict[str, Any]:
        """
        Perform complete ORB analysis for a single day.
        
        Args:
            df: DataFrame with OHLC data
            target_date: Date string in format 'YYYY-MM-DD'
            market_context: MarketContext instance for context filtering (optional)
            context_policy: 'strict' allows only alignment-matching trades; 'soft' allows mixed if extra conditions pass
            min_1h_strength: For soft policy, minimum 1H trend strength in trade direction to permit 'mixed'
            max_orb_pct: For soft policy, ORB range percent threshold (range/price) to permit 'mixed'
            max_liq_distance_pct: For soft policy, max distance to nearby liquidity beyond breakout side to permit 'mixed'
            enable_fakeouts: If True, check for fakeout entries (failed breakouts) when no clean breakout occurs
            
        Returns:
            Dictionary containing complete analysis results
        """
        # Step 1: Get ORB range
        range_high, range_low = self.calculate_orb_range(df, target_date)
        
        if range_high is None or range_low is None:
            return {
                'date': target_date,
                'status': 'No ORB candle',
                'range_high': None,
                'range_low': None,
                'range_size': None,
                'breakout': None
            }
        
        range_size = range_high - range_low
        
        # Step 2: Check for breakouts
        breakout = self.detect_orb_breakout(df, target_date, range_high, range_low)

        # Step 3: Context filtering
        context_info = None
        context_alignment = None
        if market_context is not None:
            # Get context for the target date (ensure UTC-aware to match data)
            context_info = market_context.get_full_context(pd.to_datetime(target_date, utc=True))
            context_alignment = context_info.get('trend_alignment', {}).get('alignment', None)

        # Only allow trade if context gate passes
        trade_allowed = True
        gate_reason = None
        if breakout and market_context is not None:
            sig = breakout['signal_type']
            # Last price proxy: use breakout candle close
            price = breakout['entry_price']
            range_size = range_high - range_low

            if context_policy == 'strict':
                if sig == 'BUY' and context_alignment not in ['bullish', 'weak_bullish']:
                    trade_allowed, gate_reason = False, 'strict_mismatch'
                elif sig == 'SELL' and context_alignment not in ['bearish', 'weak_bearish']:
                    trade_allowed, gate_reason = False, 'strict_mismatch'
            else:  # soft policy
                def _has_liquidity_incentive(ctx: Dict[str, Any]) -> bool:
                    liq = ctx.get('liquidity_pools', {})
                    if sig == 'BUY':
                        # look for equal/swing highs above range_high within distance
                        candidates = (liq.get('equal_highs', []) or []) + (liq.get('swing_highs', []) or [])
                        for lvl in candidates:
                            if lvl > range_high and (lvl - range_high) / price <= max_liq_distance_pct:
                                return True
                    else:  # SELL
                        candidates = (liq.get('equal_lows', []) or []) + (liq.get('swing_lows', []) or [])
                        for lvl in candidates:
                            if lvl < range_low and (range_low - lvl) / price <= max_liq_distance_pct:
                                return True
                    return False

                def _one_hour_supports(ctx: Dict[str, Any]) -> bool:
                    one_h = ctx.get('1h_trend', {})
                    dir_ok = (sig == 'BUY' and one_h.get('direction') == 'bullish') or (sig == 'SELL' and one_h.get('direction') == 'bearish')
                    return bool(dir_ok and (one_h.get('strength', 0) >= min_1h_strength))

                def _orb_is_small() -> bool:
                    # Use current price to normalize
                    return (range_size / price) <= max_orb_pct

                # Opposite weak alignment is still risky; require stronger confirmation
                if sig == 'BUY' and context_alignment in ['bearish', 'weak_bearish']:
                    if not (_one_hour_supports(context_info) and _has_liquidity_incentive(context_info)):
                        trade_allowed, gate_reason = False, 'soft_opposite_without_support'
                elif sig == 'SELL' and context_alignment in ['bullish', 'weak_bullish']:
                    if not (_one_hour_supports(context_info) and _has_liquidity_incentive(context_info)):
                        trade_allowed, gate_reason = False, 'soft_opposite_without_support'
                elif context_alignment == 'mixed':
                    # Allow if any of the supporting conditions is true
                    if not (_one_hour_supports(context_info) or _has_liquidity_incentive(context_info) or _orb_is_small()):
                        trade_allowed, gate_reason = False, 'soft_mixed_without_support'

        # Step 4: If no valid breakout and fakeouts enabled, check for fakeout entry
        fakeout = None
        if enable_fakeouts and (not breakout or not trade_allowed):
            fakeout = self.detect_fakeout(df, target_date, range_high, range_low)
            
            # Apply context filtering to fakeout as well
            if fakeout and market_context is not None:
                sig = fakeout['signal_type']
                price = fakeout['entry_price']
                
                # Fakeout context gate: require 1H to support the fakeout direction
                one_h = context_info.get('1h_trend', {}) if context_info else {}
                fakeout_supported = (
                    (sig == 'BUY' and one_h.get('direction') == 'bullish' and one_h.get('strength', 0) >= min_1h_strength) or
                    (sig == 'SELL' and one_h.get('direction') == 'bearish' and one_h.get('strength', 0) >= min_1h_strength)
                )
                
                if not fakeout_supported:
                    fakeout = None  # Filter out fakeout if 1H doesn't support

        return {
            'date': target_date,
            'status': 'Fakeout' if fakeout else ('Breakout' if breakout and trade_allowed else 'No breakout'),
            'range_high': range_high,
            'range_low': range_low,
            'range_size': range_size,
            'breakout': breakout if trade_allowed else None,
            'fakeout': fakeout,
            'context': context_info if market_context is not None else None,
            'context_policy': context_policy,
            'gate_reason': gate_reason
        }
    
    def print_day_analysis(self, analysis: Dict[str, Any]):
        """
        Print formatted analysis results for a single day.
        
        Args:
            analysis: Results from analyze_single_day()
        """
        date = analysis['date']
        print(f"\n📅 {date}")
        print("-" * 30)
        
        if analysis['status'] == 'No ORB candle':
            print("❌ No ORB candle found")
            return
        
        range_high = analysis['range_high']
        range_low = analysis['range_low']
        range_size = analysis['range_size']
        
        print(f"📊 ORB Range: {range_high:.1f} - {range_low:.1f} ({range_size:.1f} pts)")
        
        breakout = analysis['breakout']
        if breakout:
            signal = breakout['signal_type']
            entry = breakout['entry_price']
            risk = breakout['risk']
            time = breakout['breakout_time'].strftime('%H:%M')
            
            print(f"🚨 {signal} signal at {time} UTC")
            print(f"   Entry: {entry:.1f}, Risk: {risk:.1f} pts")
        else:
            print("📈 No breakout - stayed in range")
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the strategy configuration.
        
        Returns:
            Dictionary containing strategy parameters
        """
        return {
            'strategy_name': 'Opening Range Breakout (ORB)',
            'orb_period': '8:00-8:15 London time (07:00 UTC)',
            'entry_method': 'Close-based breakout',
            'stop_loss_method': f'{self.stop_buffer_points} points from candle open',
            'take_profit_method': '1:1 Risk/Reward ratio',
            'timezone': 'UTC data, London session timing'
        }