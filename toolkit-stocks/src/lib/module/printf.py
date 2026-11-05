import os
from datetime import datetime
from enum import StrEnum


class printf:
	_file = None
	_path = None
	_to_console = True
	_create_log = True
	_last_msg = None
	_last_level = None
	_last_msg_counter = 1
	_last_ts = None

	@classmethod
	def open(cls, directory: str = "log", create_log: bool = True, console_print: bool = True):
		"""Open a new log file with timestamped name inside the given directory if create_log is True."""
		cls._create_log = create_log
		cls._to_console = console_print

		if cls._create_log:
			os.makedirs(directory, exist_ok=True)
			timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
			cls._path = os.path.join(directory, f"{timestamp}.log")
			cls._file = open(cls._path, "a", encoding="utf-8")

	@classmethod
	def close(cls):
		"""Flush pending duplicate summary, then close the log file."""
		cls._flush_pending()
		if cls._file:
			timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			cls._write_line(f"[{timestamp}] [INFO] Log ended successfully")
			cls._file.flush()
			cls._file.close()
			cls._file = None

	def __new__(cls, message: str = "", level: str = "INFO"):
		"""Log a message. Duplicates of (message, level) are suppressed; when duplication
		ends, one summary line is emitted with the newest timestamp and total count."""
		is_duplicate = cls._last_msg == message and cls._last_level == level

		if is_duplicate:
			cls._last_msg_counter += 1
			cls._last_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			return None

		# duplication ended (or this is the first message) — emit pending summary, then the new line
		cls._flush_pending()

		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		cls._last_msg = message
		cls._last_level = level
		cls._last_msg_counter = 1
		cls._last_ts = timestamp

		cls._write_line(f"[{timestamp}] [{level}] {message}")
		return None

	@classmethod
	def _flush_pending(cls):
		"""If the last message had duplicates, write its summary line (newest timestamp + count)."""
		if cls._last_msg is None or cls._last_msg_counter <= 1:
			return
		cls._write_line(f"[{cls._last_ts}] [{cls._last_level}] {cls._last_msg} ({cls._last_msg_counter})")

	@classmethod
	def _write_line(cls, msg_row):
		if cls._create_log and cls._file:
			cls._file.write(f"{msg_row}\n")
			cls._file.flush()
		if cls._to_console:
			print(msg_row, flush=True)


class level(StrEnum):
	INFO = "INFO"
	WARNING = "WARNING"
	ERROR = "ERROR"
	DEBUG = "DEBUG"
