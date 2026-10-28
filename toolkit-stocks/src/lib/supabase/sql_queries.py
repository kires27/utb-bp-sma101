
import constants.db_tables as dbt


def query_insert(table_name, data: dict) -> list[str, list]:
	'''data: key-value pair works like column-row pair'''

	columns = ", ".join(data.keys())
	placeholders = ", ".join(["%s"] * len(data))
	values = list(data.values())
	if table_name in dbt.statement_tables:
		columns += ", updated_at"
		placeholders += ", now()"

	query = f"""
		INSERT INTO {table_name} ({columns})
		VALUES ({placeholders})
		ON CONFLICT DO NOTHING;
	"""

	return [query, values]


def query_upsert(table_name, data: dict, conflict_keys: dict) -> list[str, list]:
	"""
	Create an UPSERT query for PostgreSQL.
	The main purpose if mainly for updating but if the
	row doesn't exist yet, then insertion takes place.

	! This method cannot be used with identity keys (auto-generated), eg. {id: 8}

	Parameters:
	- table_name: the table name
	- data: dict of column-value pairs to insert/update, e.g. {"price": 150, "volume": 2000}
	- conflict_keys: dict of key-value pairs to detect conflict, e.g. {"symbol": "AAPL"}
	
	Returns:
	[query string, list of values]
	"""
	if not conflict_keys: raise ValueError("'where' conditions is empty")

	columns = ", ".join(data.keys())
	placeholders = ", ".join(["%s"] * len(data))
	conflict_cols = ", ".join(conflict_keys.keys())
	update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in data.keys()])
	if table_name in dbt.statement_tables:
		update_clause += ", updated_at = now()"

	query = f"""
		INSERT INTO {table_name} ({columns})
		VALUES ({placeholders})
		ON CONFLICT ({conflict_cols})
		DO UPDATE SET {update_clause}
	"""

	values = list(data.values())
	return [query, values]
