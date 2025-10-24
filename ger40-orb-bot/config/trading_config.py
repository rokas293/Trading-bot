"""
Trading Configuration - Expose tuning thresholds without editing code

Adjust these values to control context filtering and fakeout behavior.
"""

# Context policy: 'strict' or 'soft'
CONTEXT_POLICY = 'soft'

# Soft policy thresholds
MIN_1H_STRENGTH = 30  # Minimum 1H trend strength to allow mixed alignment
MAX_ORB_PCT = 0.004  # 0.4% - ORB range as % of price to allow mixed
MAX_LIQ_DISTANCE_PCT = 0.005  # 0.5% - Max distance to liquidity beyond breakout

# Fakeout setup
ENABLE_FAKEOUTS = True  # If True, trade failed breakouts (wick through, close back)

# ORB Strategy base settings (inherited from settings.py if not overridden)
STOP_BUFFER_POINTS = 5.0  # Points to place stop loss away from candle structure
