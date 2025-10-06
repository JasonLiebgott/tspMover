# Save as: switching_backtest.py
# Requirements: pandas, numpy, yfinance, pandas_dataread    ism = None
    print("WARNING: ISM PMI series not found. Please provide 'ism_pmi.csv' or adjust code to fetch PMI.")

# -----------------------
# PREPARE MONTHLY SIGNALS
# -----------------------tlib, scipy
# pip install pandas numpy yfinance pandas_datareader matplotlib scipy

import pandas as pd
import numpy as np
import yfinance as yf
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
from datetime import datetime
import scipy.stats as st

yf.pdr_override()

# -----------------------
# USER PARAMETERS
# -----------------------
START = "1995-01-01" # backtest start
END = datetime.today().strftime("%Y-%m-%d")
REBALANCE_FREQ = 'M' # monthly rebalance
TRANSACTION_COST = 0.0005 # 5 bps per trade (one-way)
# Asset proxies (change if you prefer different proxies)
ASSETS = {
"SPY": 0.6, # S&P 500 (growth core)
"IWM": 0.2, # small caps
"VEU": 0.2 # international (broad)
}
PROTECTION_PROXY = "SHY" # short-term Treasury proxy (G-fund proxy)
CASH_PROXY = "BIL" # alternative cash proxy (optional)

# Strategy thresholds (as discussed)
THRESHOLDS = {
"PE_forward_red": 22.0, # forward P/E > 22 -> red
"ERP_red": 0.02, # equity risk premium < 2% -> red
"PMI_red": 48.0, # ISM PMI < 48 -> macro red
"PMI_green": 52.0, # PMI > 52 -> macro green
"unemp_rise_pct": 0.2, # 3-mo avg unemp rising by 0.2 ppt -> macro red
"yieldcurve_inv": 0.0, # 10y - 3m spread <= 0 -> warning/red
"corecpi_red": 4.0, # core CPI >= 4% -> rates red
"corecpi_green": 3.0, # core CPI < 3% -> rates green
"real_yield_red": 0.02, # 10y real yield >= 2% -> rates red
"real_yield_green": 0.01 # 10y real yield < 1% -> rates green
}

# Allocation rules
ALLOCATION = {
# all green: stay fully in growth (use ASSETS weights)
"all_green": {"growth": 1.00, "protection": 0.00},
# one red (partial protection)
"one_red": {"growth": 0.75, "protection": 0.25},
# two red (heavy protection)
"two_red": {"growth": 0.40, "protection": 0.60},
# three red (mostly protection)
"three_red": {"growth": 0.10, "protection": 0.90}
}

# -----------------------
# DATA FETCHING
# -----------------------
def fetch_prices(tickers, start=START, end=END):
df = yf.download(list(tickers), start=start, end=end, progress=False)['Adj Close']
df = df.ffill().dropna(how='all')
return df

def fetch_fred_series(series, start=START, end=END):
return pdr.DataReader(series, 'fred', start, end).dropna()

# Pull asset prices
tickers = list(ASSETS.keys()) + [PROTECTION_PROXY, CASH_PROXY, "IEF"] # IEF used for 10y proxy if needed
prices = fetch_prices(tickers)

# Fetch Treasury yields and CPI (via FRED)
try:
cpi_core = fetch_fred_series('CORECPIA0', START, END) # CORE CPI - US All Items Less Food & Energy (if available)
except Exception:
# alternate core CPI name if the above isn't available; user may need to adjust
cpi_core = fetch_fred_series('CPILFESL', START, END)

ten_year = fetch_fred_series('DGS10', START, END) # 10-year nominal yield
t10_breakeven = fetch_fred_series('T10YIE', START, END) # 10-yr breakeven (try); if not available the code will handle missing
unemp = fetch_fred_series('UNRATE', START, END) # unemployment rate

# ISM PMI series: there is no official FRED series for ISM manufacturing PMI, user may need to input or we load from csv
# For now assume a CSV 'ism_pmi.csv' with Date and PMI columns if not available via API
try:
ism = fetch_fred_series('NAPM', START, END) # sometimes available
except Exception:
try:
ism = pd.read_csv('ism_pmi.csv', parse_dates=['Date'], index_col='Date')['PMI']
except Exception:
ism = None
print("WARNING: ISM PMI series not found. Please provide 'ism_pmi.csv' or adjust code to fetch PMI.")

# Load Shiller CAPE
cape = pd.read_csv(SHILLER_CSV_PATH, parse_dates=['Date'], index_col='Date')
cape = cape.asfreq('M').ffill()

# -----------------------
# PREPARE MONTHLY SIGNALS
# -----------------------
# Monthly resample for prices (use month-end)
monthly_prices = prices.resample('M').last().dropna(how='all')
monthly_returns = monthly_prices.pct_change().dropna()

# Prepare indicator series aligned monthly (end-of-month)
cpi_core_m = cpi_core.resample('M').last().ffill()
ten_year_m = ten_year.resample('M').last().ffill()
try:
t10_breakeven_m = t10_breakeven.resample('M').last().ffill()
except Exception:
t10_breakeven_m = None

unemp_m = unemp.resample('M').last().ffill()
if ism is not None:
ism_m = ism.resample('M').last().ffill()
else:
ism_m = None

cape_m = cape.resample('M').last().ffill()

# Compute forward P/E approx: use SPY price / (12-month trailing earnings from yfinance earnings if available)
# If not available, user can provide forward P/E CSV
# As fallback compute trailing P/E using SPY price / (SP500 annual earnings proxy) => approximate only
# For now we'll leave forward_PE as NaN if not found
forward_pe = pd.Series(index=monthly_prices.index, dtype=float)

# Equity risk premium (ERP) simple approx: earnings yield (1 / trailing PE) - 10y yield
# We'll approximate trailing PE using CAPE (not ideal, but workable) -> use 1/CAPE as proxy of earnings yield
erp = pd.Series(index=monthly_prices.index, dtype=float)
erp.loc[cape_m.index] = (1.0 / cape_m['CAPE'].values) - (ten_year_m.reindex(cape_m.index).values / 100.0)

# Compose signal table
signal_df = pd.DataFrame(index=monthly_prices.index)
signal_df['CAPE'] = cape_m['CAPE'].reindex(signal_df.index)
signal_df['10y'] = ten_year_m['DGS10'].reindex(signal_df.index)
signal_df['coreCPI'] = cpi_core_m.reindex(signal_df.index)
signal_df['unemp'] = unemp_m['UNRATE'].reindex(signal_df.index)
if ism_m is not None:
signal_df['PMI'] = ism_m.reindex(signal_df.index)
signal_df['erp'] = erp

# Compute 3-month moving avg unemp and delta
signal_df['unemp_3m'] = signal_df['unemp'].rolling(3).mean()
signal_df['unemp_12m'] = signal_df['unemp'].rolling(12).mean()
signal_df['unemp_delta'] = signal_df['unemp_3m'] - signal_df['unemp_12m']

# Yield curve proxy: 10y - 3m (approx using 3m Treasury from FRED if available)
try:
dgs3 = fetch_fred_series('DGS3MO', START, END).resample('M').last().ffill()
signal_df['yc_10_3m'] = signal_df['10y'] - dgs3.reindex(signal_df.index)['DGS3MO']
except Exception:
signal_df['yc_10_3m'] = np.nan

# Compute 10y real yield (approx)
if t10_breakeven_m is not None:
signal_df['10y_real'] = (signal_df['10y']/100.0) - t10_breakeven_m.reindex(signal_df.index)['T10YIE']
else:
# approximation: real yield = nominal - (core CPI yoy)
cpi_yoy = signal_df['coreCPI'].pct_change(12)
signal_df['10y_real'] = (signal_df['10y']/100.0) - cpi_yoy

# -----------------------
# SIGNAL RULES (Red/Neutral/Green)
# -----------------------
def color_flag(val, green_thr, red_thr, higher_is_bad=True):
"""Return 'RED', 'NEUTRAL', 'GREEN' for a metric where higher_is_bad indicates direction."""
if pd.isna(val):
return 'NEUTRAL'
if higher_is_bad:
if val >= red_thr:
return 'RED'
elif val < green_thr:
return 'GREEN'
else:
return 'NEUTRAL'
else:
# lower_is_bad (e.g., ERP: lower ERP is bad)
if val <= red_thr:
return 'RED'
elif val > green_thr:
return 'GREEN'
else:
return 'NEUTRAL'

# Evaluate at each month
flags = []
for idx, row in signal_df.iterrows():
val_flags = {}
# Valuation layer
val_flags['CAPE_flag'] = color_flag(row['CAPE'], THRESHOLDS['CAPE_green'], THRESHOLDS['CAPE_red'], higher_is_bad=True)
# ERP: lower is bad
val_flags['ERP_flag'] = color_flag(row['erp'], THRESHOLDS['ERP_red'], THRESHOLDS['ERP_red'], higher_is_bad=False)
# Forward PE not implemented reliably => approximate with CAPE fold if needed. We'll skip forward PE in logic for now.

# Macro layer
if not np.isnan(row.get('PMI', np.nan)):
val_flags['PMI_flag'] = color_flag(row['PMI'], THRESHOLDS['PMI_green'], THRESHOLDS['PMI_red'], higher_is_bad=False)
else:
val_flags['PMI_flag'] = 'NEUTRAL'
# Unemployment rising?
val_flags['unemp_flag'] = 'RED' if row['unemp_delta'] > THRESHOLDS['unemp_rise_pct'] else 'GREEN' if row['unemp_delta'] < -THRESHOLDS['unemp_rise_pct'] else 'NEUTRAL'
# Yield curve
if not np.isnan(row.get('yc_10_3m', np.nan)):
val_flags['yc_flag'] = 'RED' if row['yc_10_3m'] <= THRESHOLDS['yieldcurve_inv'] else 'GREEN'
else:
val_flags['yc_flag'] = 'NEUTRAL'

# Rates & Inflation
val_flags['corecpi_flag'] = color_flag(row['coreCPI'], THRESHOLDS['corecpi_green'], THRESHOLDS['corecpi_red'], higher_is_bad=True)
val_flags['real_yield_flag'] = color_flag(row['10y_real'], THRESHOLDS['real_yield_green'], THRESHOLDS['real_yield_red'], higher_is_bad=True)

flags.append((idx, val_flags))

flag_df = pd.DataFrame({d[0]: d[1] for d in flags}).T
flag_df.index = pd.to_datetime(flag_df.index)

# -----------------------
# AGGREGATE LAYER FLAGS (VAL / MACRO / RATES)
# -----------------------
def layer_color(row):
# Valuation: use CAPE_flag and ERP_flag -> if either RED => valuation red; if both green => green; otherwise neutral
valuations = [row['CAPE_flag'], row['ERP_flag']]
if 'RED' in valuations:
val = 'RED'
elif valuations.count('GREEN') == len(valuations):
val = 'GREEN'
else:
val = 'NEUTRAL'
# Macro: PMI_flag, unemp_flag, yc_flag -> majority rule
macro_votes = [row['PMI_flag'], row['unemp_flag'], row['yc_flag']]
if macro_votes.count('RED') >= 2:
mac = 'RED'
elif macro_votes.count('GREEN') >= 2:
mac = 'GREEN'
else:
mac = 'NEUTRAL'
# Rates: corecpi_flag, real_yield_flag -> if either RED => rates red; both green => green
rates_votes = [row['corecpi_flag'], row['real_yield_flag']]
if 'RED' in rates_votes:
rat = 'RED'
elif rates_votes.count('GREEN') == len(rates_votes):
rat = 'GREEN'
else:
rat = 'NEUTRAL'
return pd.Series({'Valuation': val, 'Macro': mac, 'Rates': rat})

layer_flags = flag_df.apply(layer_color, axis=1)

# -----------------------
# ALLOCATION DECISION & BACKTEST
# -----------------------
def decide_allocation(flags_row):
red_count = sum(1 for v in flags_row if v == 'RED')
if red_count == 0:
return ALLOCATION['all_green']
elif red_count == 1:
return ALLOCATION['one_red']
elif red_count == 2:
return ALLOCATION['two_red']
else:
return ALLOCATION['three_red']

allocations = layer_flags.apply(decide_allocation, axis=1)

# Build portfolio returns - monthly rebalancing
# Growth portion is split across ASSETS proportionally
growth_weights = pd.Series(ASSETS)
asset_returns = monthly_prices[list(ASSETS.keys())].pct_change().dropna()
prot_returns = monthly_prices[PROTECTION_PROXY].pct_change().dropna()
combined_index = asset_returns.join(prot_returns, how='outer').ffill().dropna()

# Align allocation dates with return index
alloc_dates = combined_index.index.intersection(allocations.index)
alloc_sub = allocations.reindex(alloc_dates)
layer_flags_sub = layer_flags.reindex(alloc_dates)

# Initialize portfolio
port_vals = []
cash = 1.0
current_weights = None
portfolio_value = 1.0
portfolio_history = pd.DataFrame(index=alloc_dates, columns=['Portfolio'])

prev_weights = None

for date in alloc_dates:
# compute allocation
alloc = alloc_sub.loc[date] # dict with growth/protection fractions
growth_frac = alloc['growth']
prot_frac = alloc['protection']
# growth weight vector (across ASSETS)
gw = growth_weights / growth_weights.sum()
# full weights
weights = {}
for k in ASSETS.keys():
weights[k] = gw[k] * growth_frac
weights[PROTECTION_PROXY] = prot_frac
# normalize (just in case)
total_w = sum(weights.values())
for k in weights:
weights[k] /= total_w

# compute monthly return from weights and returns (use returns for this date)
ret_row = combined_index.loc[date]
# Where missing returns exist, treat as 0 for that month (or forward-fill earlier)
r = 0.0
for ticker, w in weights.items():
if ticker in ret_row and not np.isnan(ret_row[ticker]):
r += w * ret_row[ticker]
else:
r += 0.0

# apply transaction cost for turnover from prev_weights
turnover_cost = 0.0
if prev_weights is not None:
# compute total absolute change in weight
all_tickers = set(list(prev_weights.keys()) + list(weights.keys()))
change = sum(abs(weights.get(t, 0.0) - prev_weights.get(t, 0.0)) for t in all_tickers)
turnover_cost = change * TRANSACTION_COST
portfolio_value = portfolio_value * (1.0 + r) * (1.0 - turnover_cost)
prev_weights = weights.copy()
portfolio_history.loc[date, 'Portfolio'] = portfolio_value

# Buy & hold benchmark: equal mix of growth basket (ASSETS) with no rebalancing (simple)
bh_weights = growth_weights / growth_weights.sum()
bh_returns = (asset_returns[list(ASSETS.keys())] * bh_weights).sum(axis=1)
bh_val = (1 + bh_returns).cumprod()
bh_val = bh_val.reindex(portfolio_history.index).ffill().fillna(method='bfill')

# -----------------------
# METRICS & PLOT
# -----------------------
pf = portfolio_history['Portfolio'].dropna()
rets = pf.pct_change().dropna()
ann_return = (pf.iloc[-1]) ** (12.0 / len(pf)) - 1
ann_vol = rets.std() * np.sqrt(12)
sharpe = (rets.mean() * 12) / (rets.std() * np.sqrt(12)) if ann_vol > 0 else np.nan
# max drawdown
cum = pf
running_max = cum.cummax()
drawdown = (cum - running_max) / running_max
maxdd = drawdown.min()

print("Backtest period:", pf.index[0].strftime('%Y-%m-%d'), "to", pf.index[-1].strftime('%Y-%m-%d'))
print("Final portfolio value:", pf.iloc[-1])
print(f"Annualized return (approx): {ann_return:.2%}")
print(f"Annualized vol (approx): {ann_vol:.2%}")
print(f"Sharpe (approx): {sharpe:.2f}")
print(f"Max drawdown: {maxdd:.2%}")

# How often did we go to heavy protection?
protection_share = alloc_sub.apply(lambda x: x['protection'], axis=1)
pct_time_heavy = (protection_share >= 0.6).mean()
print(f"Percent months with protection >= 60%: {pct_time_heavy:.1%}")

# Plot
plt.figure(figsize=(10,6))
plt.plot(pf.index, pf.values, label='Switching Portfolio')
plt.plot(bh_val.index, bh_val.values / bh_val.iloc[0] * pf.iloc[0], label='Buy & Hold Growth Basket')
plt.title('Switching Framework Backtest')
plt.legend()
plt.xlabel('Date')
plt.ylabel('Portfolio Value (normalized)')
plt.grid(True)
plt.tight_layout()
plt.savefig('switching_backtest_plot.png')
print("Plot saved to switching_backtest_plot.png")