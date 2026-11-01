import traceback
from psycopg2 import errors as p_errors
from psycopg2 import sql
from datetime import date as dtdate, datetime as dt_datetime

from psycopg2.extras import execute_values

from lib.supabase.sql_queries import query_insert, query_upsert
from lib.functions.helper import evaluate_null_tolerance
from lib.functions.data_types import to_date
from lib.module.printf import printf, level as lv
from lib.supabase.init import get_connection
import constants.db_tables as dbt


def get_stock_id(symbol: str) -> int | None:
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT id FROM {} WHERE symbol = %s").format(sql.Identifier(dbt.stock)),
			(symbol,)
		)
		result = cursor.fetchone()

		if result is None:
			raise ValueError(f"Stock ({symbol}) isn't in database")

		return result[0]
	except Exception as e:
		printf(e, lv.WARNING)
		return None


def get_stock_id_map(symbols: list[str]) -> dict[str, int]:
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT symbol, id FROM {} WHERE symbol = ANY(%s)").format(sql.Identifier(dbt.stock)),
			(symbols,)
		)
		return {row[0]: row[1] for row in cursor.fetchall()}
	except Exception as e:
		printf(f"get_stock_id_map failed: {e}", lv.WARNING)
		return {}


def get_symbol_exchanges() -> dict[str, str | None]:
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT symbol, exchange FROM {}").format(sql.Identifier(dbt.stock))
		)
		return {row[0]: row[1] for row in cursor.fetchall()}
	except Exception as e:
		printf(f"get_symbol_exchanges failed: {e}", lv.WARNING)
		return {}


def get_symbols() -> list:
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT symbol FROM {}").format(sql.Identifier(dbt.stock))
		)
		results = cursor.fetchall()
	except Exception as e:
		printf(f"get_symbols failed: {e}", lv.WARNING)
		return []

	if not results:
		printf("No data fetched from database", lv.WARNING)
		return []

	return [row[0] for row in results]


def get_symbol_meta(symbols: list[str]) -> dict[str, dict]:
	'''symbol -> {name, exchange, currency} for existing stock rows.'''
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT symbol, name, exchange, currency FROM {} WHERE symbol = ANY(%s)").format(sql.Identifier(dbt.stock)),
			(symbols,)
		)
		return {
			row[0]: {"name": row[1], "exchange": row[2], "currency": row[3]}
			for row in cursor.fetchall()
		}
	except Exception as e:
		printf(f"get_symbol_meta failed: {e}", lv.WARNING)
		return {}


def get_latest_dates(table: str, stock_ids: list[int]) -> dict[int, dtdate]:
	'''stock_id -> newest date present in table (batch variant of get_latest_date).'''
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("""
				SELECT stock_id, max(date)
				FROM {}
				WHERE stock_id = ANY(%s)
				GROUP BY stock_id
			""").format(sql.Identifier(table)),
			(stock_ids,)
		)
		return {row[0]: to_date(row[1]) for row in cursor.fetchall()}
	except Exception as e:
		printf(f"get_latest_dates failed: {e}", lv.WARNING)
		return {}


def get_latest_market_times(stock_ids: list[int]) -> dict[int, dt_datetime]:
	'''stock_id -> newest stored regular_market_time (tz-aware) from stock_metric.
	Hourly gating: fetch/write only when the market time is newer than stored.'''
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("""
				SELECT stock_id, regular_market_time
				FROM {}
				WHERE stock_id = ANY(%s) AND regular_market_time IS NOT NULL
			""").format(sql.Identifier(dbt.metric)),
			(stock_ids,)
		)
		return {row[0]: row[1] for row in cursor.fetchall()}
	except Exception as e:
		printf(f"get_latest_market_times failed: {e}", lv.WARNING)
		return {}


def get_latest_fiscal_dates(table: str, stock_ids: list[int]) -> dict[int, dtdate]:
	'''stock_id -> newest fiscal_date present in table (statements use fiscal_date, not date).'''
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("""
				SELECT stock_id, max(fiscal_date)
				FROM {}
				WHERE stock_id = ANY(%s)
				GROUP BY stock_id
			""").format(sql.Identifier(table)),
			(stock_ids,)
		)
		return {row[0]: to_date(row[1]) for row in cursor.fetchall()}
	except Exception as e:
		printf(f"get_latest_fiscal_dates failed: {e}", lv.WARNING)
		return {}


def get_fresh_stock_ids(table: str, stock_ids: list[int], cutoff: dtdate) -> set[int]:
	'''stock_ids whose newest fiscal_date >= cutoff (fresh, safe to skip).'''
	latest = get_latest_fiscal_dates(table, stock_ids)
	return {sid for sid, d in latest.items() if d >= cutoff}


def get_stamped_stock_ids(table: str, stock_ids: list[int]) -> set[int]:
	'''stock_ids whose rows all carry an updated_at stamp (NULL stamps = legacy).'''
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("""
				SELECT stock_id
				FROM {}
				WHERE stock_id = ANY(%s)
				GROUP BY stock_id
				HAVING count(*) FILTER (WHERE updated_at IS NULL) = 0
			""").format(sql.Identifier(table)),
			(stock_ids,)
		)
		return {row[0] for row in cursor.fetchall()}
	except Exception as e:
		printf(f"get_stamped_stock_ids failed: {e}", lv.WARNING)
		return set()


def touch_statement_rows(table: str, stock_ids: list[int]):
	'''Bump updated_at for a symbol's rows without refetching (staleness clock).'''
	if not stock_ids:
		return
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("UPDATE {} SET updated_at = now() WHERE stock_id = ANY(%s)")
			.format(sql.Identifier(table)),
			(stock_ids,)
		)
		conn.commit()
	except Exception as e:
		printf(f"touch_statement_rows failed: {e}", lv.WARNING)
		conn.rollback()


def get_latest_date(table, stock_id, start_date="2000-01-01") -> dtdate:
	conn = get_connection()
	cursor = conn.cursor()

	cursor.execute(
		sql.SQL("""
			SELECT date
			FROM {}
			where stock_id = %s
			ORDER BY date DESC
			LIMIT 1
		""").format(sql.Identifier(table)),
		(stock_id,)
	)
	result = cursor.fetchone()

	if not result:
		printf("No data fetched from database", lv.WARNING)
		return dtdate.fromisoformat(start_date)

	return to_date(result[0])


def get_statements_by_stock(stock_id: int, table: str, limit: int = 5) -> list[dict]:
	"""
	Returns:
		list of objects containing financial statements.
		sorted by newest first.
	"""
	conn = get_connection()
	cursor = conn.cursor()

	cursor.execute(
		f"SELECT * FROM {table} WHERE stock_id = %s ORDER BY fiscal_date DESC LIMIT {limit}",
		[stock_id]
	)
	rows = cursor.fetchall()

	if not rows:
		raise ValueError(f"{table} statement is empty")
		# printf("No data fetched from database", lv.ERROR)
		return []

	columns = [desc[0] for desc in cursor.description]
	return [dict(zip(columns, row)) for row in rows]


def insert_data_statement(
	statements: list | dict,
	db_table: str,
	null_tolerance=1,
	update_condition: dict = {},
	conflict_keys: list[str] | None = None
) -> int:
	"""
	:null_tolerance - value 1 means allow all
	:conflict_keys - column names forming the unique key; when set, rows are
		upserted (ON CONFLICT ... DO UPDATE) instead of inserted (DO NOTHING)
	:return - number of rows actually inserted/updated (excludes NULL-skips and duplicates)
	"""
	conn = get_connection()
	cursor = conn.cursor()
	inserted = 0

	try:
		if not isinstance(statements, (list, dict)):
			raise TypeError(f"statement has wrong data type: {type(statements)}")
		if not statements:
			conn.rollback()
			return 0  # nothing to insert - not an error

		obj_list = statements if isinstance(statements, list) else [statements]

		for obj in obj_list:
			if update_condition:
				query, row = query_upsert(db_table, obj, update_condition)
			elif conflict_keys:
				query, row = query_upsert(
					db_table, obj, {col: obj[col] for col in conflict_keys}
				)
			else:
				query, row = query_insert(db_table, obj)
			
			passed_nulls, cleaned_row = evaluate_null_tolerance(row, null_tolerance)
			if not passed_nulls:
				printf("skipped statement object due to many NULLS in data", lv.INFO)
				continue

			cursor.execute(query, cleaned_row)

			if cursor.rowcount == 0:
				printf("Skipped duplicate row", lv.INFO)
			else:
				inserted += cursor.rowcount
				printf("Inserted row", lv.INFO)

		conn.commit()
		return inserted

	except (ValueError, TypeError) as e:
		tb = traceback.extract_tb(e.__traceback__)[-1]
		printf(f"{e} (File '{tb.filename}', line {tb.lineno})", lv.WARNING)
		conn.rollback()
	except p_errors.UniqueViolation as e:
		tb = traceback.extract_tb(e.__traceback__)[-1]
		printf(f"Insert failed, the row already exists. (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		conn.rollback()
	except Exception as e:
		tb = traceback.extract_tb(e.__traceback__)[-1]
		printf(f"{e} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		conn.rollback()
		return 0
	finally:
		cursor.close()


def insert_rows_bulk(
	table: str,
	rows: list[dict],
	conflict_keys: list[str] | None = None,
	null_tolerance: float = 1,
) -> int:
	'''
	Chunked bulk insert via execute_values. conflict_keys set -> upsert
	(ON CONFLICT ... DO UPDATE, every non-key column updated from EXCLUDED);
	without -> plain insert (ON CONFLICT DO NOTHING). Rows whose columns are
	over the null tolerance are dropped before flush.
	:return - rows flushed (dropped rows excluded).
	'''
	conn = get_connection()
	cursor = conn.cursor()

	try:
		if not rows:
			return 0

		# column set from first row; evaluate null tolerance row-wise
		flush: list[tuple] = []
		dropped = 0
		for row in rows:
			passed_nulls, cleaned = evaluate_null_tolerance(row, null_tolerance)
			if passed_nulls:
				flush.append(tuple(cleaned.get(col) for col in rows[0].keys()))
			else:
				dropped += 1
		if dropped:
			printf(f"{table}: dropped {dropped} rows over null tolerance", lv.INFO)
		if not flush:
			return 0

		cols = list(rows[0].keys())
		col_sql = ", ".join(sql.Identifier(c).as_string(conn) for c in cols)
		placeholders = "(" + ", ".join(["%s"] * len(cols)) + ")"
		if conflict_keys:
			key_sql = ", ".join(sql.Identifier(c).as_string(conn) for c in conflict_keys)
			update_sql = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in conflict_keys)
			statement = (
				f"INSERT INTO {table} ({col_sql}) VALUES %s "
				f"ON CONFLICT ({key_sql}) DO UPDATE SET {update_sql}"
			)
		else:
			statement = f"INSERT INTO {table} ({col_sql}) VALUES %s ON CONFLICT DO NOTHING"

		execute_values(cursor, statement, flush, page_size=len(flush))
		conn.commit()
		return len(flush)
	except Exception as e:
		tb = traceback.extract_tb(e.__traceback__)[-1]
		printf(f"{e} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		conn.rollback()
		return 0
	finally:
		cursor.close()


class RowFlusher:
	'''
	Streaming row buffer for a phase: rows accumulate across symbols and are
	flushed to the DB in chunks of flush_size via insert_rows_bulk. Keeps the
	universe out of memory and replaces per-row cursor.execute inserts.
	finish() drains the remainder and returns total rows flushed.
	'''

	def __init__(self, table: str, flush_size: int = 1000, conflict_keys: list[str] | None = None, null_tolerance: float = 1):
		self.table = table
		self.flush_size = flush_size
		self.conflict_keys = conflict_keys
		self.null_tolerance = null_tolerance
		self.buffer: list[dict] = []
		self.written = 0

	def add(self, rows: list[dict]):
		if rows:
			self.buffer.extend(rows)
			if len(self.buffer) >= self.flush_size:
				self._flush()

	def _flush(self):
		rows, self.buffer = self.buffer, []
		self.written += insert_rows_bulk(
			self.table, rows,
			conflict_keys=self.conflict_keys,
			null_tolerance=self.null_tolerance,
		)

	def finish(self) -> int:
		if self.buffer:
			self._flush()
		return self.written
