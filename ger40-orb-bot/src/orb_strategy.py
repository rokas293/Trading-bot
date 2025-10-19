"""
ORB Strategy Module for GER40 Trading Bot

This module contains the core Opening Range Breakout strategy implementation.
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime


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
    
    def analyze_single_day(self, df: pd.DataFrame, target_date: str) -> Dict[str, Any]:
        """
        Perform complete ORB analysis for a single day.
        
        Args:
            df: DataFrame with OHLC data
            target_date: Date string in format 'YYYY-MM-DD'
            
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
        
        return {
            'date': target_date,
            'status': 'Breakout' if breakout else 'No breakout',
            'range_high': range_high,
            'range_low': range_low,
            'range_size': range_size,
            'breakout': breakout
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