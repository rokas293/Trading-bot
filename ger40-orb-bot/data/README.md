# GER40 Data

This folder contains historical GER40 (German DAX) price data for backtesting the ORB strategy.

## Data Files

- **FOREXCOM_GER40, 15 (3).csv** - 15-minute candle data (Oct 2024 - Oct 2025)
  - Format: time, open, high, low, close, Up Marker, Down Marker
  - Size: 21,861 rows covering full year
  - Date Range: October 31, 2024 to October 3, 2025
  - Timezone: UTC
  - Used for comprehensive ORB strategy analysis
  - Results: 238 trading days, 100% breakout detection rate

## Historical Data (Removed)

- **GER40_15m_7days.csv** - Previous 7-day dataset (replaced with full year data)

## Data Requirements

The ORB strategy requires:

- 15-minute timeframe data
- OHLC format (Open, High, Low, Close)
- UTC timezone
- London session coverage (07:00-16:00 UTC)

## Usage

```python
from src.data_handler import DataHandler

# Load data
handler = DataHandler("data/GER40_15m_7days.csv")
df = handler.load_data()

# Validate data quality
handler.validate_data_integrity()
```

## Data Source

Data sourced from ForexCom/Trading.com platform for educational/research purposes.
