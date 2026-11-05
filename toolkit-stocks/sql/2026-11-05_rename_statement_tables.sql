-- Group financial statements under a shared "statement" prefix.
ALTER TABLE stock_balance_sheet	RENAME TO stock_statement_balance;
ALTER TABLE stock_cash_flow		RENAME TO stock_statement_cash;
ALTER TABLE stock_income_statement RENAME TO stock_statement_income;
