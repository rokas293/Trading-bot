# GER40 ORB Trading Bot

A comprehensive Opening Range Breakout (ORB) trading strategy implementation for GER40 (DAX) with multi-timeframe context filtering, machine learning readiness, and advanced debugging.

## 🎯 Project Overview

This project implements an intelligent ORB trading strategy that:

- Identifies the 8:00-8:15 London session opening range
- Uses multi-timeframe context (Daily/4H/1H) to filter trades
- Implements strict and soft context policies for flexible participation
- Detects fakeout patterns (failed breakouts)
- Provides comprehensive backtesting with win rate and profit factor analysis
- Built with ML feature engineering foundations

## 🚀 Latest Update (October 2025)

### **Context-Aware Trading: 123% Profit Increase**

Implemented multi-timeframe context filtering that dramatically improved performance:

**Strict vs Soft Policy Results (Oct 2024 - Oct 2025):**

| Metric              | Strict Policy | Soft Policy | Improvement |
| ------------------- | ------------- | ----------- | ----------- |
| Trades              | 113           | 188         | +66%        |
| Win Rate            | 58.4%         | 60.1%       | +1.7pp      |
| Total P&L           | +€2,145.90    | +€4,780.34  | +123%       |
| Profit Factor       | 1.41          | 1.54        | +9%         |
| Daily Participation | 47.5%         | 79%         | +66%        |

### **What Changed**

1. **✅ Multi-Timeframe Context Module** (`src/market_context.py`)

   - Analyzes Daily, 4H, and 1H trend directions and strengths
   - Detects liquidity pools (swing highs/lows, equal levels)
   - Calculates weighted trend alignment scores

2. **✅ Strict Policy** (Conservative)

   - Only takes trades when higher timeframe alignment matches breakout direction
   - BUY requires: bullish or weak_bullish context
   - SELL requires: bearish or weak_bearish context

3. **✅ Soft Policy** (Intelligent)

   - Allows mixed alignment when microstructure confirms:
     - 1H trend supports with strength ≥ 30, OR
     - Nearby liquidity pool within 0.5% of price, OR
     - Small ORB range (≤ 0.4% of price)
   - Maintains quality while increasing frequency

4. **✅ Fakeout Detection** (`detect_fakeout`)

   - Identifies failed breakouts (wick through range, close back inside)
   - Trades reversal when 1H trend supports
   - Adds setup diversity for choppy markets

5. **✅ Configurable Parameters** (`config/trading_config.py`)
   - Tune thresholds without editing code
   - Easy A/B testing of different settings

## 📊 Data & Analysis

### **Multi-Timeframe Dataset**

- **15-Minute**: FOREXCOM_GER40, 15 (3).csv (21,861 candles)
- **1-Hour**: FOREXCOM_GER40, 60.csv (5,615 candles)
- **4-Hour**: FOREXCOM_GER40, 240.csv (1,430 candles)
- **Daily**: FOREXCOM_GER40, 1D.csv (240 candles)
- **Coverage**: October 31, 2024 to October 3, 2025
- **Alignment**: All timeframes trimmed to matching date range

### **Strategy Configuration**

- **ORB Period**: 8:00-8:15 London (7:00 UTC single candle)
- **Entry Method**: Close-based breakout confirmation
- **Risk Management**: 5-point stop buffer, 1% account risk per trade
- **Context Policy**: Strict or Soft (configurable)
- **Fakeout Setup**: Optional (1H confirmation required)

## 🛠️ Technical Architecture

```
ger40-orb-bot/
├── src/
│   ├── orb_strategy.py          # ✅ Core strategy with context integration
│   ├── market_context.py        # ✅ Multi-timeframe analysis
│   ├── data_handler.py          # ✅ FOREXCOM format support
│   └── ml_enhanced_orb.py       # 🔄 ML integration (next phase)
├── tests/
│   ├── complete_dataset_analysis.py    # ✅ Full year analysis
│   ├── trade_count_with_context.py     # ✅ Trade frequency counts
│   ├── compare_context_policies.py     # ✅ Strict vs soft comparison
│   └── backtest_with_metrics.py        # ✅ Win rate & profit factor
├── data/
│   ├── FOREXCOM_GER40, 15 (3).csv     # 15-minute candles
│   ├── FOREXCOM_GER40, 60.csv         # 1-hour candles
│   ├── FOREXCOM_GER40, 240.csv        # 4-hour candles
│   ├── FOREXCOM_GER40, 1D.csv         # Daily candles
│   └── README.md                       # Dataset documentation
├── config/
│   ├── settings.py              # ✅ Base configuration
│   └── trading_config.py        # ✅ Tuning parameters
├── docs/
│   └── context_policies.md      # ✅ Context filtering documentation
└── results/                     # Generated analysis outputs
```

## 🔧 Context Filtering Logic

### **Strict Policy**

```python
if signal == 'BUY' and alignment not in ['bullish', 'weak_bullish']:
    block_trade()
if signal == 'SELL' and alignment not in ['bearish', 'weak_bearish']:
    block_trade()
```

### **Soft Policy**

```python
if alignment == 'mixed':
    allow_if:
        1H_trend_supports(strength >= 30) OR
        liquidity_nearby(distance <= 0.5%) OR
        small_range(range_pct <= 0.4%)
```

## 📈 Usage Examples

### **Run Full Backtest with Metrics**

```bash
cd ger40-orb-bot
python tests/backtest_with_metrics.py
```

Output includes: trade counts, win rate, profit factor, final balance

### **Compare Strict vs Soft Policies**

```bash
python tests/compare_context_policies.py
```

### **Count Trades with Context**

```bash
python tests/trade_count_with_context.py
```

### **Single Day Analysis with Context**

```python
from src.orb_strategy import ORBStrategy
from src.market_context import MarketContext
from src.data_handler import DataHandler

strategy = ORBStrategy()
mc = MarketContext(data_dir="data")
handler = DataHandler("data/FOREXCOM_GER40, 15 (3).csv")
df = handler.load_data()

analysis = strategy.analyze_single_day(
    df, '2025-10-02',
    market_context=mc,
    context_policy='soft',
    enable_fakeouts=True
)
print(analysis)
```

## ⚙️ Configuration

Edit `config/trading_config.py` to tune strategy parameters:

```python
CONTEXT_POLICY = 'soft'           # 'strict' or 'soft'
MIN_1H_STRENGTH = 30              # 1H trend strength threshold
MAX_ORB_PCT = 0.004               # 0.4% - ORB range size limit
MAX_LIQ_DISTANCE_PCT = 0.005      # 0.5% - Liquidity proximity
ENABLE_FAKEOUTS = True            # Enable/disable fakeout entries
```

## 🎯 ML Readiness

The strategy is built with machine learning integration in mind:

**Available Features:**

- Trend directions (Daily/4H/1H): categorical
- Trend strengths (0-100): numeric
- Trend alignment score: numeric
- Liquidity pool proximity: numeric
- ORB range characteristics: numeric
- Timeframe agreement counts: numeric

**Labeled Data:**

- Every trade has outcome (win/loss)
- Context features stored with each trade
- Ready for binary classification

**Next Steps:**

1. Collect labeled dataset (backtest with outcomes)
2. Train classifier to predict win probability
3. Compare rule-based vs ML performance
4. Implement hybrid approach (ML confidence + rules)

## 📚 Documentation

- **Context Policies**: See `docs/context_policies.md`
- **Dataset Info**: See `data/README.md`
- **Configuration**: See `config/trading_config.py`

## 🚀 Recent Achievements

### **Phase 1: Debugging (Completed)**

- Fixed 7 critical bugs in ORB implementation
- Achieved 100% breakout detection rate
- Established realistic baseline performance

### **Phase 2: Context Filtering (Completed)**

- Implemented multi-timeframe analysis
- Created strict and soft policies
- Increased daily participation to 79%
- Improved profit by 123%
- Added fakeout detection

### **Phase 3: ML Integration (In Progress)**

- Feature engineering foundation complete
- Rule-based baseline established (60% win rate, 1.54 PF)
- Ready for classifier training and hybrid approach

## 📋 Requirements

```bash
pip install pandas numpy python-dateutil
```

## 🤝 Development Notes

This project represents a comprehensive debugging and optimization case study, transforming a flawed trading strategy implementation into a robust, well-tested system. The systematic approach to identifying and fixing bugs provides valuable insights for algorithmic trading development.

**Key Learning**: Always validate strategy assumptions against manual backtesting and ensure proper data handling throughout the pipeline.

---

**Status**: ✅ **Debugging Phase Complete** | 🔄 **Ready for ML Enhancement**
