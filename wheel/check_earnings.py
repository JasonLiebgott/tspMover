import pandas as pd

df = pd.read_excel('wheel_candidates_20260102_0843.xlsx')

# Check INTC options
intc = df[df['ticker'] == 'INTC'].sort_values('composite_score', ascending=False)
print('INTC options with earnings info:')
print(intc[['ticker', 'expiry', 'strike', 'composite_score', 'earnings_risk', 'earnings_days_diff']].head(15).to_string())

print('\n' + '='*80)
print('Options with earnings risk TRUE:')
risk = df[df['earnings_risk'] == True]
print(f'Total: {len(risk)}')
if len(risk) > 0:
    print(risk[['ticker', 'expiry', 'strike', 'earnings_days_diff', 'earnings_risk']].head(20).to_string())
