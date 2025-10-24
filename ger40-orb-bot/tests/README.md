# ORB Strategy Testing Suite

This directory contains comprehensive testing and analysis scripts for the GER40 Opening Range Breakout (ORB) trading strategy.

## 📋 Test Scripts Overview

### **Performance Analysis**

#### `backtest_with_metrics.py` ⭐ **Primary Backtest**

Full-featured backtesting with realistic trade simulation and performance metrics.

**Features:**

- Complete trade lifecycle tracking (entry → TP/SL outcome)
- Realistic position sizing (1% account risk)
- Win rate, profit factor, total P&L calculation
- Context policy comparison (strict vs soft)
- Fakeout setup integration

**Usage:**

```bash
python tests/backtest_with_metrics.py
```

**Output:**

```
=== BACKTEST RESULTS (SOFT POLICY) ===
Total ORB Days: 238
Total Trades: 188
Win Rate: 60.1% (113 wins / 75 losses)
Total Profit/Loss: +€4,780.34
Final Balance: €14,780.34
Profit Factor: 1.54
```

---

#### `complete_dataset_analysis.py` 📊 **Baseline Analysis**

Analyzes the entire dataset to establish strategy baseline performance.

**Features:**

- Full year coverage (Oct 2024 - Oct 2025)
- Breakout detection rate validation
- Day-by-day trade log generation
- Basic P&L tracking

**Usage:**

```bash
python tests/complete_dataset_analysis.py
```

**Output:**

- Total trading days analyzed
- Breakout detection success rate
- Daily trade summaries
- Overall win/loss statistics

---

### **Context Policy Testing**

#### `compare_context_policies.py` 🔄 **Policy Comparison**

Side-by-side comparison of strict vs soft context filtering policies.

**Purpose:**

- Evaluate trade frequency differences
- Compare participation rates
- Analyze filtering effectiveness

**Usage:**

```bash
python tests/compare_context_policies.py
```

**Output:**

```
Strict Policy: 113 trades (47.5% of days)
Soft Policy: 188 trades (79.0% of days)
Difference: +75 trades (+66% increase)
```

---

#### `trade_count_with_context.py` 📈 **Trade Counter**

Quick utility to count total trades with context filtering enabled.

**Purpose:**

- Fast trade frequency check
- Verify context integration
- Monitor daily participation rate

**Usage:**

```bash
python tests/trade_count_with_context.py
```

**Output:**

```
Total ORB Days: 238
Total Trades: 188
Participation Rate: 79.0%
```

---

### **Data Validation**

#### `test_datahandler.py` ✅ **Data Handler Tests**

Unit tests for the DataHandler class to ensure correct data loading.

**Tests:**

- FOREXCOM format compatibility
- Column renaming (time → datetime)
- Datetime parsing
- Data integrity checks

**Usage:**

```bash
python tests/test_datahandler.py
```

---

## 🎯 Testing Workflow

### **Step 1: Validate Data Loading**

```bash
python tests/test_datahandler.py
```

Ensures data files load correctly before running strategy tests.

---

### **Step 2: Establish Baseline**

```bash
python tests/complete_dataset_analysis.py
```

Confirms 100% breakout detection rate and establishes performance baseline.

---

### **Step 3: Count Trades with Context**

```bash
python tests/trade_count_with_context.py
```

Quick check to see how many trades pass context filtering.

---

### **Step 4: Compare Policies**

```bash
python tests/compare_context_policies.py
```

Evaluate strict vs soft policy trade frequencies.

---

### **Step 5: Full Performance Backtest**

```bash
python tests/backtest_with_metrics.py
```

Complete analysis with win rate, profit factor, and realistic P&L.

---

## 📊 Key Metrics Tracked

### **Trade Execution**

- Total ORB days analyzed
- Total trades executed
- Daily participation rate (%)
- Breakout detection success rate

### **Performance**

- Win rate (TP hits / total trades)
- Profit factor (gross profit / gross loss)
- Total P&L (€)
- Final account balance (€)

### **Context Filtering**

- Strict policy trades vs soft policy trades
- Context alignment distribution (bullish/bearish/mixed)
- Gate reason tracking (why trades allowed/blocked)
- 1H trend strength distribution

### **Risk Management**

- Position sizes per trade (CFD contracts)
- Risk per trade (€100 fixed or 1% account)
- Risk points per trade
- TP/SL fill rates

---

## 🔧 Configuration

All tests read from `config/trading_config.py`:

```python
CONTEXT_POLICY = 'soft'           # 'strict' or 'soft'
MIN_1H_STRENGTH = 30              # 1H trend minimum
MAX_ORB_PCT = 0.004               # 0.4% range limit
MAX_LIQ_DISTANCE_PCT = 0.005      # 0.5% liquidity proximity
ENABLE_FAKEOUTS = True            # Fakeout entries
```

Modify these parameters to test different strategy configurations.

---

## 📝 Output Files

Tests generate output in the `results/` directory:

- `complete_analysis_YYYYMMDD.txt` - Full dataset analysis
- `backtest_report_YYYYMMDD.csv` - Trade-by-trade results
- `policy_comparison_YYYYMMDD.txt` - Strict vs soft comparison

---

## 🚀 Advanced Usage

### **Custom Date Range**

Modify any test script to analyze specific periods:

```python
# In backtest_with_metrics.py
start_date = '2025-01-01'
end_date = '2025-03-31'
date_range = pd.date_range(start=start_date, end=end_date, freq='B')
```

### **Test Different Policies**

Edit `config/trading_config.py` and re-run tests:

```python
# Test strict policy
CONTEXT_POLICY = 'strict'

# Test soft policy with tighter thresholds
CONTEXT_POLICY = 'soft'
MIN_1H_STRENGTH = 50  # More restrictive
MAX_ORB_PCT = 0.003   # Smaller ranges only
```

### **Enable/Disable Fakeouts**

```python
# Test without fakeout entries
ENABLE_FAKEOUTS = False
```

---

## 🐛 Debugging

### **Low Trade Count**

If participation rate is unexpectedly low:

1. Check `CONTEXT_POLICY` in `config/trading_config.py`
2. Review `MIN_1H_STRENGTH` threshold (lower = more trades)
3. Verify data files are loaded correctly
4. Check date range includes valid trading days

### **100% Win Rate (Unrealistic)**

Indicates stop loss logic may not be working:

1. Verify 5-point buffer is applied correctly
2. Check TP/SL tracking scans post-entry candles
3. Ensure datetime filtering excludes ORB period

### **No Trades Executed**

1. Confirm data files exist in `data/` directory
2. Check datetime format matches FOREXCOM structure
3. Verify timezone handling (should be UTC-aware)
4. Run `test_datahandler.py` first

---

## 📚 Related Documentation

- **Strategy Overview**: See `../README.md`
- **Context Policies**: See `../docs/context_policies.md`
- **Data Format**: See `../data/README.md`
- **Configuration**: See `../config/trading_config.py`

---

**Last Updated**: October 2025  
**Test Coverage**: 238 trading days (Oct 2024 - Oct 2025)  
**Validation Status**: ✅ All tests passing
