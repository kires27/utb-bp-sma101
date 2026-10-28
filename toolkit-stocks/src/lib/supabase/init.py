import psycopg2, os
from psycopg2 import OperationalError
from lib.module.printf import printf, level as lv


_connection = None


def get_connection():
	"""Return a live connection, reconnecting if necessary."""
	global _connection

	try:
		if _connection is None or _connection.closed != 0:
			_connection = psycopg2.connect(os.getenv("DATABASE_URL"))

			printf("Database connection established/re-established!", lv.INFO)
	except OperationalError as e:
		printf(f"Failed to connect: {e}", lv.ERROR)
		raise

	return _connection
