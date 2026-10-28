import traceback

import pandas as pd

from lib.functions.data_types import price_history_cutoff
from lib.module.printf import printf, level as lv


BATCH_SIZE = 500


class DefeatBetaSource:
	'''
	Bulk data source over the DefeatBeta Hugging Face parquet dataset (US market).
	One DuckDB query per dataset per symbol batch - no per-symbol HTTP requests.
	'''

	def __init__(self):
		from defeatbeta_api.client.duckdb_client import get_duckdb_client
		from defeatbeta_api.client.hugging_face_client import HuggingFaceClient

		self._client = get_duckdb_client()
		self._hf = HuggingFaceClient()

	def _url(self, table: str) -> str:
		return self._hf.get_url_path(table)

	def _query(self, sql: str):
		try:
			return self._client.query(sql)
		except Exception as err:
			tb = traceback.extract_tb(err.__traceback__)[-1]
			printf(f"DefeatBeta query failed: {err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
			return None

	def _chunks(self, symbols: list[str]):
		for i in range(0, len(symbols), BATCH_SIZE):
			yield symbols[i:i + BATCH_SIZE]

	@staticmethod
	def _in_clause(symbols: list[str]) -> str:
		return ", ".join("'" + s.replace("'", "''") + "'" for s in symbols)

	def us_members(self, symbols: list[str]) -> set[str]:
		'''Symbols present in the DefeatBeta US profile dataset (batch lookup).'''
		found: set[str] = set()
		for chunk in self._chunks(symbols):
			sql = f"SELECT DISTINCT symbol FROM read_parquet('{self._url('stock_profile')}') WHERE symbol IN ({self._in_clause(chunk)})"
			df = self._query(sql)
			if df is not None and not df.empty:
				found.update(df["symbol"].tolist())
		return found

	def profiles(self, symbols: list[str]) -> dict[str, dict]:
		'''symbol -> profile record dict (DefeatBeta column names).'''
		out: dict[str, dict] = {}
		for chunk in self._chunks(symbols):
			sql = f"SELECT * FROM read_parquet('{self._url('stock_profile')}') WHERE symbol IN ({self._in_clause(chunk)})"
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out[row["symbol"]] = row.to_dict()
		return out

	def officers(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''symbol -> list of officer record dicts.'''
		out: dict[str, list[dict]] = {}
		for chunk in self._chunks(symbols):
			sql = f"SELECT * FROM read_parquet('{self._url('stock_officers')}') WHERE symbol IN ({self._in_clause(chunk)})"
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out.setdefault(row["symbol"], []).append(row.to_dict())
		return out

	def statements(self, symbols: list[str], finance_type: str, period_type: str = "annual") -> dict[str, list[dict]]:
		'''
		symbol -> list of {report_date, item_name, item_value} sorted by report_date desc.
		One row per (symbol, report_date, item_name) - long format.
		'''
		out: dict[str, list[dict]] = {}
		for chunk in self._chunks(symbols):
			sql = f"""
				SELECT symbol, report_date, item_name, item_value
				FROM read_parquet('{self._url('stock_statement')}')
				WHERE symbol IN ({self._in_clause(chunk)})
					AND finance_type = '{finance_type}'
					AND period_type = '{period_type}'
					AND report_date != 'TTM'
			"""
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out.setdefault(row["symbol"], []).append({
					"report_date": row["report_date"],
					"item_name": row["item_name"],
					"item_value": row["item_value"],
				})
		for rows in out.values():
			rows.sort(key=lambda r: r["report_date"], reverse=True)
		return out

	def prices(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''symbol -> price history rows sorted by date desc: {date, open, high, low, close, volume}.'''
		out: dict[str, list[dict]] = {}
		cutoff = price_history_cutoff()
		for chunk in self._chunks(symbols):
			sql = f"""
				SELECT symbol, report_date, open, high, low, close, volume
				FROM read_parquet('{self._url('stock_prices')}')
				WHERE symbol IN ({self._in_clause(chunk)})
					AND report_date >= '{cutoff.isoformat()}'
			"""
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out.setdefault(row["symbol"], []).append({
					"date": str(row["report_date"]),
					"open": row["open"],
					"high": row["high"],
					"low": row["low"],
					"close": row["close"],
					"volume": row["volume"],
				})
		for rows in out.values():
			rows.sort(key=lambda r: r["date"], reverse=True)
		return out

	def dividends(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''symbol -> [{date, amount}] sorted by date desc.'''
		out: dict[str, list[dict]] = {}
		for chunk in self._chunks(symbols):
			sql = f"""
				SELECT symbol, report_date, amount
				FROM read_parquet('{self._url('stock_dividend_events')}')
				WHERE symbol IN ({self._in_clause(chunk)})
			"""
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out.setdefault(row["symbol"], []).append({
					"date": str(row["report_date"]),
					"amount": row["amount"],
				})
		for rows in out.values():
			rows.sort(key=lambda r: r["date"], reverse=True)
		return out

	def splits(self, symbols: list[str]) -> dict[str, list[dict]]:
		'''symbol -> [{date, factor}] with "a:b" parsed to a/b float, sorted by date desc.'''
		out: dict[str, list[dict]] = {}
		for chunk in self._chunks(symbols):
			sql = f"""
				SELECT symbol, report_date, split_factor
				FROM read_parquet('{self._url('stock_split_events')}')
				WHERE symbol IN ({self._in_clause(chunk)})
			"""
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out.setdefault(row["symbol"], []).append({
					"date": str(row["report_date"]),
					"factor": parse_split_factor(row["split_factor"]),
				})
		for rows in out.values():
			rows.sort(key=lambda r: r["date"], reverse=True)
		return out

	def shares_outstanding(self, symbols: list[str]) -> dict[str, float | None]:
		'''symbol -> latest shares_outstanding value.'''
		out: dict[str, float | None] = {}
		for chunk in self._chunks(symbols):
			sql = f"""
				SELECT symbol, arg_max(shares_outstanding, report_date) AS latest_shares
				FROM read_parquet('{self._url('stock_shares_outstanding')}')
				WHERE symbol IN ({self._in_clause(chunk)})
				GROUP BY symbol
			"""
			df = self._query(sql)
			if df is None:
				continue
			for _, row in df.iterrows():
				out[row["symbol"]] = None if pd.isna(row["latest_shares"]) else float(row["latest_shares"])
		return out


def parse_split_factor(raw) -> float | None:
	'''Parse split factor values like "5:1", 5.0 or "5.0" into a float.'''
	try:
		if raw is None:
			return None
		text = str(raw).strip()
		if ":" in text:
			num, den = text.split(":", 1)
			num_f, den_f = float(num), float(den)
			if den_f == 0:
				return None
			return num_f / den_f
		return float(text)
	except (ValueError, AttributeError):
		return None
