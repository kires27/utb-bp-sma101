import traceback
from datetime import datetime, timezone

from domain.financial_quality_score.quality_score import calculate_quality_score
from lib.supabase.sql_functions import get_statements_by_stock
from lib.module.printf import printf, level as lv
import constants.db_tables as dbt


def build_quality_score(stock_id: int) -> dict:
	try:
		if stock_id is None:
			raise TypeError("stock_id is None")

		cash_flows = get_statements_by_stock(stock_id, dbt.cash_flow, 1)

		fiscal_date = cash_flows[0].get("fiscal_date").isoformat()
		period = "TTM"

		quality_score = calculate_quality_score(stock_id, fiscal_date, period)

		return {
			"data": {
				"stock_id": stock_id,
				"fiscal_date": fiscal_date,
				"period": period,
				"maintenance_update": datetime.now(timezone.utc).isoformat(),

				"quality_score": quality_score["quality_score"],
				"median_comparison": quality_score["median_comparison"]

			},
			"fiscal_date": fiscal_date,
			"period": period,
		}
	except Exception as err:
		tb = traceback.extract_tb(err.__traceback__)[-1]
		printf(f"{err} (File '{tb.filename}', line {tb.lineno})", lv.ERROR)
		return {}
