from stock_analyzer.fetch import compare_with_competitors
from stock_analyzer.fetch_estab_year import get_founding_date

date = get_founding_date('TSLA')

print("Returned:", date)