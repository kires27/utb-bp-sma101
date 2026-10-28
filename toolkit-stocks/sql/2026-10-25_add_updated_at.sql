-- Track when statement rows were last fetched/written, for freshness-based
-- skipping in run_statements (see pipeline/statements.py).
-- Nullable, no default: NULL means "not yet stamped" = treated as stale so a
-- fresh run refetches and stamps existing rows.
ALTER TABLE stock_balance_sheet	ADD COLUMN IF NOT EXISTS updated_at timestamptz;
ALTER TABLE stock_cash_flow		ADD COLUMN IF NOT EXISTS updated_at timestamptz;
ALTER TABLE stock_income_statement ADD COLUMN IF NOT EXISTS updated_at timestamptz;
