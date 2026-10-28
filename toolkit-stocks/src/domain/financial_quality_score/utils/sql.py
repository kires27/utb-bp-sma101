from lib.supabase.init import get_connection
from psycopg2 import sql
from lib.module.printf import printf, level as lv
import constants.db_tables as dbt


def get_stock_industry(stock_id: int) -> str | None:
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT industry FROM {} WHERE id = %s").format(sql.Identifier(dbt.stock)),
			(stock_id,)
		)
		result = cursor.fetchone()

		if result is None:
			raise ValueError(f"Stock id: ({stock_id}) isn't in database")

		return result
	except Exception as e:
		printf(e, lv.WARNING)
		return None


def get_stock_ids_within_industry(industry: str):
	conn = get_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			sql.SQL("SELECT id FROM {} WHERE industry = %s").format(sql.Identifier(dbt.stock)),
			(industry,)
		)
		result = cursor.fetchall()

		if result is None:
			raise ValueError(f"Stock ({industry}) isn't in database")

		return result
	except Exception as e:
		printf(e, lv.WARNING)
		return None


def get_financial_analysis(stock_ids: list[int], fiscal_date: str, period: str) -> dict[int, dict]:
	"""
	SELECT * FROM stock_financial_analysis
	WHERE stock_id IN stock_ids AND fiscal_date = fiscal_date
	Returns {stock_id: {metric_col: value, ...}}
	"""
	if not stock_ids:
		return {}

	conn = get_connection()
	cursor = conn.cursor()

	placeholders = sql.SQL(", ").join(sql.Placeholder() * len(stock_ids))
	query = sql.SQL(
		"SELECT * FROM {} WHERE stock_id IN ({}) AND fiscal_date = %s AND period = %s"
	).format(sql.Identifier(dbt.analysis), placeholders)

	cursor.execute(query, [*stock_ids, fiscal_date, period])
	rows = cursor.fetchall()

	if not rows:
		printf("No financial analysis data found", lv.WARNING)
		return {}

	columns = [desc[0] for desc in cursor.description]
	result = {}
	for row in rows:
		record = dict(zip(columns, row))
		result[record["stock_id"]] = record

	return result
