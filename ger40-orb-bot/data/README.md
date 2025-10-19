# GER40 Data

This folder contains historical GER40 (German DAX) price data for backtesting the ORB strategy.

## Data Files

- **GER40_15m_7days.csv** - 15-minute candle data for the last 7 days
  - Format: time, open, high, low, close
  - Timezone: UTC
  - Used for ORB strategy testing (London session: 8:00-8:15 GMT = 07:00 UTC)

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
