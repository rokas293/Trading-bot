# GER40 Data

This folder contains historical GER40 (German DAX) price data across multiple timeframes for backtesting the ORB strategy.

## Data Files

### **Primary Dataset - 15-Minute Timeframe**

- **FOREXCOM_GER40, 15 (3).csv** - 15-minute candle data
  - Format: time, open, high, low, close, Up Marker, Down Marker
  - Size: 21,861 rows
  - Date Range: October 31, 2024 to October 3, 2025
  - Timezone: UTC
  - Trading Days: 238 days analyzed
  - Purpose: Primary ORB strategy execution and backtesting

### **Higher Timeframe Data - For Context & ML Features**

- **FOREXCOM_GER40, 60.csv** - 1-Hour candle data

  - Size: 5,615 rows
  - Date Range: October 31, 2024 to October 3, 2025 (aligned with 15m data)
  - Purpose: Trend analysis, higher timeframe context

- **FOREXCOM_GER40, 240.csv** - 4-Hour candle data

  - Size: 1,430 rows
  - Date Range: October 31, 2024 to October 3, 2025 (aligned with 15m data)
  - Purpose: Market structure, major trend identification

- **FOREXCOM_GER40, 1D.csv** - Daily candle data
  - Size: 240 rows
  - Date Range: November 1, 2024 to October 3, 2025 (aligned with 15m data)
  - Purpose: Daily trend context, key levels, macro structure

## Data Alignment

All timeframe datasets have been **trimmed to match the 15-minute dataset's date range** to ensure:

- Consistent analysis across all timeframes
- No data mismatches in multi-timeframe analysis
- Accurate historical context for each trading day

## Use Cases

### **ORB Strategy (15-Minute)**

- Identify 8:00-8:15 London opening range
- Detect breakout signals
- Execute trades with risk management

### **Multi-Timeframe Analysis (1H, 4H, Daily)**

- Determine higher timeframe trend direction
- Identify key support/resistance levels
- Detect liquidity pools and market structure
- Add confluence for trade filtering
- Feature engineering for machine learning

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
