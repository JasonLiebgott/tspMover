## Fixed AttributeError: 'NoneType' object has no attribute 'empty'

### 🐛 **Root Cause:**
The error occurred in `calculate_fund_metrics()` at line 1418 when trying to access `fund.returns.empty`, but `fund.returns` was `None` for some funds.

### 🔍 **Problem Analysis:**
In the `fetch_fund_data()` method, there were three possible outcomes for fund data fetching:

1. **Success**: `fund.returns` = calculated returns series ✅
2. **Exception**: `fund.returns` = empty `pd.Series()` ✅  
3. **Empty data (no exception)**: `fund.returns` = `None` ❌ **THIS CAUSED THE ERROR**

When `fund.data` was empty but no exception occurred, `fund.returns` was never initialized, leaving it as `None`.

### ✅ **Fixes Applied:**

#### 1. **Fixed Data Initialization in `fetch_fund_data()`**
```python
# BEFORE (problematic):
if not fund.data.empty:
    fund.returns = fund.data['Close'].pct_change().dropna()
    print(f"+ {fund.symbol}: {len(fund.data)} days")
else:
    print(f"✗ {fund.symbol}: No data")
    # fund.returns was left as None here!

# AFTER (fixed):
if not fund.data.empty:
    fund.returns = fund.data['Close'].pct_change().dropna()
    print(f"+ {fund.symbol}: {len(fund.data)} days")
else:
    print(f"✗ {fund.symbol}: No data")
    fund.data = pd.DataFrame()
    fund.returns = pd.Series()  # ✅ Now properly initialized
```

#### 2. **Added Safety Check in `calculate_fund_metrics()`**
```python
# BEFORE (would crash):
if fund.returns.empty:  # AttributeError if fund.returns is None
    continue

# AFTER (robust):
if fund.returns is None or fund.returns.empty:  # ✅ Handles None case
    continue
```

### 🧪 **Testing Results:**
- ✅ Funds with no data are properly skipped
- ✅ Funds with valid data are processed correctly  
- ✅ No AttributeError when `fund.returns` is `None`
- ✅ Dashboard initialization works without errors
- ✅ All syntax and import checks pass

### 🎯 **Impact:**
- **Error eliminated**: No more AttributeError crashes
- **Robust handling**: Gracefully handles all fund data states
- **No performance impact**: Minimal code changes
- **Backwards compatible**: Existing functionality unchanged

The dashboard will now run successfully even when some funds fail to fetch data from Yahoo Finance or other data sources.