"""
Data Handler Module for GER40 ORB Trading Bot

This module handles all data loading, processing, and validation operations.
"""

import pandas as pd
import os
from typing import Optional, Tuple
from datetime import datetime


class DataHandler:
    """Handles data loading and processing for the GER40 ORB trading strategy."""
    
    def __init__(self, data_file_path: str):
        """
        Initialize the DataHandler with the path to the data file.
        
        Args:
            data_file_path: Path to the CSV data file
        """
        self.data_file_path = data_file_path
        self.df: Optional[pd.DataFrame] = None
        
    def load_data(self) -> pd.DataFrame:
        """
        Load and process the GER40 data from CSV file.
        
        Returns:
            Processed DataFrame with datetime columns and additional features
            
        Raises:
            FileNotFoundError: If the data file doesn't exist
            ValueError: If the data format is invalid
        """
        if not os.path.exists(self.data_file_path):
            raise FileNotFoundError(f"Data file not found: {self.data_file_path}")
            
        print("🚀 Loading GER40 data...")
        
        # Load the raw data (FOREXCOM format doesn't need skiprows)
        self.df = pd.read_csv(self.data_file_path)
        
        # FOREXCOM format: time,open,high,low,close,Up Marker,Down Marker
        # No need to rename columns as they're already in correct format
        
        # Validate required columns
        required_columns = ['time', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Process datetime columns
        self.df['datetime'] = pd.to_datetime(self.df['time'], utc=True)
        self.df['hour'] = self.df['datetime'].dt.hour
        self.df['minute'] = self.df['datetime'].dt.minute
        self.df['date'] = self.df['datetime'].dt.date
        
        print(f"✅ Data loaded successfully!")
        print(f"Shape: {self.df.shape}")
        print(f"Columns: {self.df.columns.tolist()}")
        
        return self.df
    
    def get_data_summary(self) -> dict:
        """
        Get a summary of the loaded data.
        
        Returns:
            Dictionary containing data quality metrics
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        total_days = (self.df['datetime'].iloc[-1] - self.df['datetime'].iloc[0]).days
        
        return {
            'total_rows': len(self.df),
            'date_range_start': self.df['datetime'].iloc[0],
            'date_range_end': self.df['datetime'].iloc[-1],
            'total_days': total_days,
            'avg_candles_per_day': len(self.df) / total_days if total_days > 0 else 0,
            'missing_values': self.df.isnull().sum().to_dict(),
            'hourly_distribution': self.df['hour'].value_counts().sort_index().to_dict()
        }
    
    def print_data_summary(self):
        """Print a formatted summary of the data quality."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        summary = self.get_data_summary()
        
        print(f"\n📊 Data Quality Analysis:")
        print(f"Total rows: {summary['total_rows']:,}")
        print(f"Date range: {summary['date_range_start']} to {summary['date_range_end']}")
        print(f"Total days: {summary['total_days']}")
        print(f"Expected 15min candles per day: 96")
        print(f"Your avg candles per day: {summary['avg_candles_per_day']:.1f}")
        
        print(f"\nMissing values:")
        for col, missing in summary['missing_values'].items():
            if missing > 0:
                print(f"  {col}: {missing}")
        
        print(f"\n🕐 Trading Hours Analysis:")
        print("Hour distribution (top 10):")
        hourly_counts = summary['hourly_distribution']
        for hour in sorted(hourly_counts.keys())[:10]:
            print(f"  {hour:02d}:XX - {hourly_counts[hour]:,} candles")
    
    def get_london_session_data(self) -> pd.DataFrame:
        """
        Filter data for London trading session (8:00-17:00 GMT).
        
        Returns:
            DataFrame containing only London session data
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        # London session: 8:00-17:00 GMT = 7:00-16:00 UTC (during standard time)
        london_session = self.df[
            (self.df['hour'] >= 7) & (self.df['hour'] <= 16)
        ].copy()
        
        print(f"📍 London Session (8:00-17:00 GMT):")
        print(f"  Total candles: {len(london_session):,}")
        print(f"  Percentage of data: {len(london_session)/len(self.df)*100:.1f}%")
        
        return london_session
    
    def validate_data_integrity(self) -> bool:
        """
        Validate the integrity of the loaded data.
        
        Returns:
            True if data passes all validation checks
        """
        if self.df is None:
            return False
            
        # Check for basic data quality issues
        checks = {
            'No duplicate timestamps': self.df['datetime'].duplicated().sum() == 0,
            'High >= Low': (self.df['high'] >= self.df['low']).all(),
            'High >= Open': (self.df['high'] >= self.df['open']).all(),
            'High >= Close': (self.df['high'] >= self.df['close']).all(),
            'Low <= Open': (self.df['low'] <= self.df['open']).all(),
            'Low <= Close': (self.df['low'] <= self.df['close']).all(),
            'No negative prices': (self.df[['open', 'high', 'low', 'close']] > 0).all().all(),
            'No missing OHLC data': self.df[['open', 'high', 'low', 'close']].isnull().sum().sum() == 0
        }
        
        print(f"\n🔍 Data Integrity Checks:")
        all_passed = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        return all_passed