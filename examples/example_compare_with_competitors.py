from stock_analyzer.fetch import compare_with_competitors

# Test with one ticker
df = compare_with_competitors(
    "WMT",
    max_competitors=4
)

if df is not None:
    print("Walmart + Competitors")
    print(df.to_string())
    # Or prettier in terminal
    # print(df.round(2).to_markdown())
else:
    print("No data returned")

