"""
Configuration settings for GER40 ORB Trading Bot
"""

# Data settings
DATA_FILE_PATH = "data/GER40_15m_7days.csv"

# Strategy parameters
ORB_STRATEGY_CONFIG = {
    # Stop loss buffer in points from candle open
    'stop_buffer_points': 5.0,
    
    # ORB period timing (London time)
    'orb_start_hour_london': 8,  # 8:00 AM London
    'orb_end_hour_london': 8,    # 8:15 AM London (same hour, different minute)
    'orb_start_minute': 0,       # Start at :00
    'orb_duration_minutes': 15,  # 15-minute ORB period
    
    # Timezone conversion (London to UTC)
    'london_to_utc_offset': -1,  # London = UTC - 1 (during standard time)
    
    # Risk management
    'risk_reward_ratio': 1.0,    # 1:1 risk/reward
    'max_risk_per_trade': 100.0, # Maximum risk in points per trade
    
    # Entry criteria
    'entry_method': 'close_based',  # 'close_based' or 'touch_based'
    'min_range_size': 10.0,        # Minimum ORB range size in points
    'max_range_size': 200.0,       # Maximum ORB range size in points
}

# Backtesting settings
BACKTEST_CONFIG = {
    # Default test dates for multi-day testing
    'default_test_dates': [
        '2025-10-02',
        '2025-10-01', 
        '2025-09-30',
        '2025-09-27',
        '2025-09-26',
        '2025-09-25',
        '2025-09-24',
        '2025-09-23',
        '2024-12-20',
        '2024-12-19'
    ],
    
    # Results export settings
    'export_results': True,
    'results_filename': 'backtest_results.csv',
    'results_directory': './results/',
    
    # Verbose output settings
    'print_individual_days': True,
    'print_summary_stats': True,
    'print_detailed_results': True,
}

# Display settings
DISPLAY_CONFIG = {
    'decimal_places': 1,           # Number of decimal places for prices
    'use_emojis': False,          # Whether to use emojis in output (Windows compatibility)
    'timezone_display': 'UTC',    # Display timezone for times
    'date_format': '%Y-%m-%d',    # Date format for display
    'time_format': '%H:%M',       # Time format for display
}

# File paths
PATHS = {
    'data_directory': '../data/',
    'results_directory': './results/',
    'config_directory': './config/',
    'tests_directory': './tests/',
}

# Validation settings
VALIDATION_CONFIG = {
    'validate_data_integrity': True,
    'check_missing_orb_candles': True,
    'warn_on_high_breakout_rate': True,
    'high_breakout_rate_threshold': 90.0,  # Warn if >90% of days have breakouts
}

def get_orb_utc_hour():
    """
    Calculate the UTC hour for the ORB period based on London time.
    
    Returns:
        int: UTC hour for ORB period
    """
    london_hour = ORB_STRATEGY_CONFIG['orb_start_hour_london']
    utc_offset = ORB_STRATEGY_CONFIG['london_to_utc_offset']
    return london_hour + utc_offset

def validate_config():
    """
    Validate configuration settings for consistency.
    
    Returns:
        bool: True if configuration is valid
    """
    issues = []
    
    # Check risk/reward ratio
    if ORB_STRATEGY_CONFIG['risk_reward_ratio'] <= 0:
        issues.append("Risk/reward ratio must be positive")
    
    # Check range size limits
    if ORB_STRATEGY_CONFIG['min_range_size'] >= ORB_STRATEGY_CONFIG['max_range_size']:
        issues.append("Min range size must be less than max range size")
    
    # Check stop buffer
    if ORB_STRATEGY_CONFIG['stop_buffer_points'] <= 0:
        issues.append("Stop buffer points must be positive")
    
    # Check ORB timing
    if not (0 <= ORB_STRATEGY_CONFIG['orb_start_hour_london'] <= 23):
        issues.append("ORB start hour must be between 0 and 23")
    
    if issues:
        print("Configuration validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True

# Validate configuration on import
if __name__ == "__main__":
    if validate_config():
        print("✅ Configuration is valid")
        print(f"ORB UTC hour: {get_orb_utc_hour()}")
    else:
        print("❌ Configuration has issues")