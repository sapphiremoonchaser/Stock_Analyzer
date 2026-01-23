from stock_analyzer.fetch import compare_with_competitors

main_ticker = 'MTDR'

# Test with one ticker
df = compare_with_competitors(
    main_ticker,
    max_competitors=4
)

if df is not None:
    print(f"{main_ticker} + Competitors")
    print(df.to_string())
else:
    print("No data returned")

