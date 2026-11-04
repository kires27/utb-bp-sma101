import psycopg2, os
from psycopg2 import OperationalError
from lib.module.printf import printf, level as lv
from lib.functions.netstats import incr_db


_connection = None


class CountingCursor(psycopg2.extensions.cursor):
	'''Cursor that counts every execute/executemany as one DB request.
	psycopg2.extras.execute_values funnels through cursor.execute, so bulk
	writes are counted here too — no double counting elsewhere.'''

	def execute(self, sql, args=None):
		incr_db()
		return super().execute(sql, args)

	def executemany(self, sql, args_list):
		incr_db()
		return super().executemany(sql, args_list)


def get_connection():
	"""Return a live connection, reconnecting if necessary."""
	global _connection

	try:
		if _connection is None or _connection.closed != 0:
			_connection = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=CountingCursor)

			printf("Database connection established/re-established!", lv.INFO)
	except OperationalError as e:
		printf(f"Failed to connect: {e}", lv.ERROR)
		raise

	return _connection
