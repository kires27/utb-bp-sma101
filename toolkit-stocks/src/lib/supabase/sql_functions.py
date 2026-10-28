import traceback
from psycopg2 import errors as p_errors
from psycopg2 import sql
from datetime import date as dtdate

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

	cursor.execute(
		sql.SQL("SELECT symbol FROM {}").format(sql.Identifier(dbt.stock))
	)
	results = cursor.fetchall()

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
