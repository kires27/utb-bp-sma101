-- Drop dividend_yield from stock_quote. Added earlier today for the fa
-- phase (PLAN-fa-metric-price.md), then made redundant: the fa phase
-- computes dividend_yield itself from stock_dividend (TTM sum / current
-- price) and stores it in stock_financial_analysis. No yfinance yield
-- needed anywhere. Column was dropped live by hand; this documents it.
ALTER TABLE stock_quote DROP COLUMN IF EXISTS dividend_yield;

-- PostgREST schema cache reload.
NOTIFY pgrst, 'reload schema';
