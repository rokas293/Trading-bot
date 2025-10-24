"""
Market Context Module for Multi-Timeframe Analysis

This module provides higher timeframe context for the ORB strategy:
- Daily/4H/1H trend analysis
- Market structure identification (higher highs/lows, lower highs/lows)
- Liquidity pool detection (swing highs/lows, equal highs/lows)
- Fakeout pattern recognition
- Feature engineering for ML enhancement
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path


class MarketContext:
    """
    Analyzes multi-timeframe market context to enhance ORB strategy decisions.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the MarketContext analyzer.
        
        Args:
            data_dir: Directory containing the multi-timeframe CSV files
        """
        self.data_dir = Path(data_dir)
        self.timeframes = {}
        self._load_all_timeframes()
    
    def _load_all_timeframes(self):
        """Load all timeframe data (15m, 1H, 4H, Daily)"""
        files = {
            '15m': 'FOREXCOM_GER40, 15 (3).csv',
            '1H': 'FOREXCOM_GER40, 60.csv',
            '4H': 'FOREXCOM_GER40, 240.csv',
            'Daily': 'FOREXCOM_GER40, 1D.csv'
        }
        
        for tf, filename in files.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                df['time'] = pd.to_datetime(df['time'], utc=True)
                df = df.sort_values('time').reset_index(drop=True)
                self.timeframes[tf] = df
                print(f"Loaded {tf}: {len(df)} candles from {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
            else:
                print(f"Warning: {filepath} not found")
    
    def get_daily_trend(self, date: pd.Timestamp) -> Dict:
        """
        Calculate daily trend using simple price action analysis.
        
        Args:
            date: The date to analyze (will look back for trend)
        
        Returns:
            Dictionary with trend analysis:
            - direction: 'bullish', 'bearish', 'neutral'
            - strength: 0-100 (based on consecutive closes)
            - recent_high: highest high in last N days
            - recent_low: lowest low in last N days
        """
        if 'Daily' not in self.timeframes:
            return {'direction': 'neutral', 'strength': 0}
        
        daily_df = self.timeframes['Daily']
        
        # Get data up to (but not including) the target date
        mask = daily_df['time'].dt.date < date.date()
        relevant_data = daily_df[mask].tail(20)  # Look back 20 days
        
        if len(relevant_data) < 5:
            return {'direction': 'neutral', 'strength': 0}
        
        # Calculate trend based on close prices
        closes = relevant_data['close'].values
        
        # Simple trend: compare recent closes
        recent_5 = closes[-5:]
        avg_recent = np.mean(recent_5)
        older_5 = closes[-10:-5] if len(closes) >= 10 else closes[:-5]
        avg_older = np.mean(older_5) if len(older_5) > 0 else avg_recent
        
        # Determine direction
        if avg_recent > avg_older * 1.005:  # 0.5% threshold
            direction = 'bullish'
            # Count consecutive higher closes for strength
            strength = self._calculate_trend_strength(closes, 'bullish')
        elif avg_recent < avg_older * 0.995:
            direction = 'bearish'
            strength = self._calculate_trend_strength(closes, 'bearish')
        else:
            direction = 'neutral'
            strength = 0
        
        # Get recent structure levels
        recent_high = relevant_data['high'].max()
        recent_low = relevant_data['low'].min()
        
        return {
            'direction': direction,
            'strength': strength,
            'recent_high': recent_high,
            'recent_low': recent_low,
            'lookback_days': len(relevant_data)
        }
    
    def get_4h_trend(self, date: pd.Timestamp) -> Dict:
        """Calculate 4H trend for the given date."""
        if '4H' not in self.timeframes:
            return {'direction': 'neutral', 'strength': 0}
        
        df_4h = self.timeframes['4H']
        
        # Get 4H candles from previous day and current day up to 8:00
        start_time = date - pd.Timedelta(days=1)
        end_time = date + pd.Timedelta(hours=8)
        
        mask = (df_4h['time'] >= start_time) & (df_4h['time'] < end_time)
        relevant_data = df_4h[mask]
        
        if len(relevant_data) < 3:
            return {'direction': 'neutral', 'strength': 0}
        
        closes = relevant_data['close'].values
        
        # Calculate trend
        if len(closes) >= 6:
            recent_avg = np.mean(closes[-3:])
            older_avg = np.mean(closes[-6:-3])
        else:
            recent_avg = closes[-1]
            older_avg = closes[0]
        
        if recent_avg > older_avg * 1.003:
            direction = 'bullish'
            strength = self._calculate_trend_strength(closes, 'bullish')
        elif recent_avg < older_avg * 0.997:
            direction = 'bearish'
            strength = self._calculate_trend_strength(closes, 'bearish')
        else:
            direction = 'neutral'
            strength = 0
        
        return {
            'direction': direction,
            'strength': strength,
            'recent_high': relevant_data['high'].max(),
            'recent_low': relevant_data['low'].min()
        }
    
    def get_1h_trend(self, date: pd.Timestamp) -> Dict:
        """Calculate 1H trend for the given date."""
        if '1H' not in self.timeframes:
            return {'direction': 'neutral', 'strength': 0}
        
        df_1h = self.timeframes['1H']
        
        # Get 1H candles from last 12 hours before ORB (8:00)
        start_time = date - pd.Timedelta(hours=12)
        end_time = date + pd.Timedelta(hours=8)
        
        mask = (df_1h['time'] >= start_time) & (df_1h['time'] < end_time)
        relevant_data = df_1h[mask]
        
        if len(relevant_data) < 3:
            return {'direction': 'neutral', 'strength': 0}
        
        closes = relevant_data['close'].values
        
        # Simple trend calculation
        if len(closes) >= 6:
            recent_avg = np.mean(closes[-3:])
            older_avg = np.mean(closes[-6:-3])
        else:
            recent_avg = closes[-1]
            older_avg = closes[0]
        
        if recent_avg > older_avg * 1.002:
            direction = 'bullish'
            strength = self._calculate_trend_strength(closes, 'bullish')
        elif recent_avg < older_avg * 0.998:
            direction = 'bearish'
            strength = self._calculate_trend_strength(closes, 'bearish')
        else:
            direction = 'neutral'
            strength = 0
        
        return {
            'direction': direction,
            'strength': strength,
            'recent_high': relevant_data['high'].max(),
            'recent_low': relevant_data['low'].min()
        }
    
    def _calculate_trend_strength(self, closes: np.ndarray, direction: str) -> int:
        """
        Calculate trend strength based on consecutive moves in the trend direction.
        
        Args:
            closes: Array of closing prices
            direction: 'bullish' or 'bearish'
        
        Returns:
            Strength value 0-100
        """
        if len(closes) < 2:
            return 0
        
        consecutive_count = 0
        for i in range(len(closes) - 1, 0, -1):
            if direction == 'bullish' and closes[i] > closes[i-1]:
                consecutive_count += 1
            elif direction == 'bearish' and closes[i] < closes[i-1]:
                consecutive_count += 1
            else:
                break
        
        # Convert to 0-100 scale (max 10 consecutive = 100%)
        strength = min(100, (consecutive_count / 10) * 100)
        return int(strength)
    
    def detect_liquidity_pools(self, date: pd.Timestamp, lookback_days: int = 5) -> Dict:
        """
        Detect liquidity pools (areas of equal highs/lows, swing points).
        
        Args:
            date: The date to analyze
            lookback_days: How many days to look back for swing points
        
        Returns:
            Dictionary with liquidity zones:
            - swing_highs: List of recent swing high levels
            - swing_lows: List of recent swing low levels
            - equal_highs: Price levels with multiple touches on highs
            - equal_lows: Price levels with multiple touches on lows
        """
        if 'Daily' not in self.timeframes:
            return {}
        
        daily_df = self.timeframes['Daily']
        
        # Get recent days
        mask = (daily_df['time'].dt.date < date.date())
        relevant_data = daily_df[mask].tail(lookback_days + 2)  # +2 for swing detection
        
        if len(relevant_data) < 3:
            return {'swing_highs': [], 'swing_lows': []}
        
        swing_highs = []
        swing_lows = []
        
        # Detect swing highs (higher than neighbors)
        for i in range(1, len(relevant_data) - 1):
            if (relevant_data.iloc[i]['high'] > relevant_data.iloc[i-1]['high'] and 
                relevant_data.iloc[i]['high'] > relevant_data.iloc[i+1]['high']):
                swing_highs.append(relevant_data.iloc[i]['high'])
        
        # Detect swing lows (lower than neighbors)
        for i in range(1, len(relevant_data) - 1):
            if (relevant_data.iloc[i]['low'] < relevant_data.iloc[i-1]['low'] and 
                relevant_data.iloc[i]['low'] < relevant_data.iloc[i+1]['low']):
                swing_lows.append(relevant_data.iloc[i]['low'])
        
        # Detect equal highs/lows (within 0.1% tolerance)
        equal_highs = self._find_equal_levels(relevant_data['high'].values, tolerance=0.001)
        equal_lows = self._find_equal_levels(relevant_data['low'].values, tolerance=0.001)
        
        return {
            'swing_highs': swing_highs[-3:] if swing_highs else [],  # Keep last 3
            'swing_lows': swing_lows[-3:] if swing_lows else [],
            'equal_highs': equal_highs,
            'equal_lows': equal_lows
        }
    
    def _find_equal_levels(self, prices: np.ndarray, tolerance: float = 0.001) -> list:
        """
        Find price levels that appear multiple times (within tolerance).
        
        Args:
            prices: Array of prices
            tolerance: Percentage tolerance for "equal" (0.001 = 0.1%)
        
        Returns:
            List of price levels with multiple touches
        """
        equal_levels = []
        
        for i in range(len(prices)):
            matches = 0
            level = prices[i]
            
            for j in range(len(prices)):
                if i != j:
                    if abs(prices[j] - level) / level <= tolerance:
                        matches += 1
            
            # If we found 2+ matches and haven't added this level yet
            if matches >= 1:
                # Check if we already have a similar level
                is_new = True
                for existing in equal_levels:
                    if abs(level - existing) / existing <= tolerance:
                        is_new = False
                        break
                
                if is_new:
                    equal_levels.append(level)
        
        return equal_levels
    
    def get_full_context(self, date: pd.Timestamp) -> Dict:
        """
        Get complete multi-timeframe context for a trading day.
        
        Args:
            date: The trading date
        
        Returns:
            Dictionary with all context information
        """
        context = {
            'date': date,
            'daily_trend': self.get_daily_trend(date),
            '4h_trend': self.get_4h_trend(date),
            '1h_trend': self.get_1h_trend(date),
            'liquidity_pools': self.detect_liquidity_pools(date)
        }
        
        # Add trend alignment score
        context['trend_alignment'] = self._calculate_trend_alignment(context)
        
        return context
    
    def _calculate_trend_alignment(self, context: Dict) -> Dict:
        """
        Improved trend alignment using weighted scoring and strength thresholds.
        Returns a more realistic signal based on majority and strength.
        """
        # Assign weights: Daily=0.5, 4H=0.3, 1H=0.2
        weights = {'daily_trend': 0.5, '4h_trend': 0.3, '1h_trend': 0.2}
        directions = {}
        strengths = {}
        for tf in weights:
            directions[tf] = context[tf]['direction']
            strengths[tf] = context[tf]['strength']
        
        # Calculate weighted bullish/bearish score
        bullish_score = sum(weights[tf] * strengths[tf]/100 if directions[tf] == 'bullish' else 0 for tf in weights)
        bearish_score = sum(weights[tf] * strengths[tf]/100 if directions[tf] == 'bearish' else 0 for tf in weights)
        
        # Majority voting with strength threshold
        min_strength = 10  # Only count timeframes with at least 10% strength
        bullish_count = sum(1 for tf in weights if directions[tf] == 'bullish' and strengths[tf] >= min_strength)
        bearish_count = sum(1 for tf in weights if directions[tf] == 'bearish' and strengths[tf] >= min_strength)
        
        if bullish_score >= 0.5 and bullish_count >= 2:
            alignment = 'bullish'
            score = int(bullish_score * 100)
        elif bearish_score >= 0.5 and bearish_count >= 2:
            alignment = 'bearish'
            score = int(bearish_score * 100)
        elif bullish_score > bearish_score:
            alignment = 'weak_bullish'
            score = int(bullish_score * 100)
        elif bearish_score > bullish_score:
            alignment = 'weak_bearish'
            score = int(bearish_score * 100)
        else:
            alignment = 'mixed'
            score = int(max(bullish_score, bearish_score) * 100)
        
        return {
            'alignment': alignment,
            'score': score,
            'bullish_timeframes': bullish_count,
            'bearish_timeframes': bearish_count,
            'bullish_score': round(bullish_score, 2),
            'bearish_score': round(bearish_score, 2)
        }


def test_market_context():
    """Test the MarketContext module with sample data."""
    print("Testing MarketContext Module")
    print("=" * 60)
    
    # Initialize
    mc = MarketContext(data_dir="data")
    
    # Test on a few dates
    test_dates = [
        pd.Timestamp('2024-11-01', tz='UTC'),
        pd.Timestamp('2024-12-01', tz='UTC'),
        pd.Timestamp('2025-01-15', tz='UTC'),
        pd.Timestamp('2025-06-01', tz='UTC')
    ]
    
    for date in test_dates:
        print(f"\n{date.date()}:")
        print("-" * 60)
        
        context = mc.get_full_context(date)
        
        print(f"Daily Trend: {context['daily_trend']['direction']} "
              f"(strength: {context['daily_trend']['strength']})")
        print(f"4H Trend: {context['4h_trend']['direction']} "
              f"(strength: {context['4h_trend']['strength']})")
        print(f"1H Trend: {context['1h_trend']['direction']} "
              f"(strength: {context['1h_trend']['strength']})")
        print(f"Trend Alignment: {context['trend_alignment']['alignment']} "
              f"(score: {context['trend_alignment']['score']})")
        
        liq = context['liquidity_pools']
        print(f"Liquidity Pools:")
        print(f"  Swing Highs: {len(liq.get('swing_highs', []))} levels")
        print(f"  Swing Lows: {len(liq.get('swing_lows', []))} levels")
        print(f"  Equal Highs: {len(liq.get('equal_highs', []))} levels")
        print(f"  Equal Lows: {len(liq.get('equal_lows', []))} levels")


if __name__ == "__main__":
    test_market_context()
