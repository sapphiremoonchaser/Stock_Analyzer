from stock_analyzer.fetch import compare_with_competitors

df = compare_with_competitors(
    'AAPL',
    max_competitors=4
)

print(df[['name', 'established']])