import os
from datetime import datetime
from enum import StrEnum
# import atexit


class printf:
	_file = None
	_path = None
	_to_console = True
	_create_log = True
	_last_log_pos = None
	_last_msg = None
	_last_msg_counter = 1

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
		"""Close the log file if open."""
		if cls._file:
			timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			cls._file.write(f"[{timestamp}] [INFO] Log ended successfully\n")
			cls._file.flush()
			cls._file.close()
			cls._file = None

	def __new__(cls, message: str = "", level: str = "INFO"):
		"""Log a message to the file (if enabled) and optionally to console."""
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		msg_row = f"[{timestamp}] [{level}] {message}"

		is_duplicate = cls._last_msg == message

		if is_duplicate:
			cls._last_msg_counter += 1
		else:
			cls._last_msg_counter = 1

		if cls._create_log and cls._file:
			cls._write_file(msg_row, is_duplicate)

		if cls._to_console:
			cls._write_console(msg_row, is_duplicate)
		
		cls._last_msg = message

		return None

	@classmethod
	def _write_file(cls, msg_row, is_duplicate):
		if is_duplicate:
			cls._file.seek(cls._last_log_pos)
			cls._file.truncate()
		else:
			cls._file.seek(0, 2)
			cls._last_log_pos = cls._file.tell()

		line = f"{msg_row} ({cls._last_msg_counter})\n" if is_duplicate else f"{msg_row}\n"
		cls._file.write(line)
		cls._file.flush()

	@classmethod
	def _write_console(cls, msg_row, is_duplicate):
		if is_duplicate:
			print(f"\r{msg_row} ({cls._last_msg_counter})", end="", flush=True)
		else:
			# close previous live line
			if cls._last_msg is not None: print()
			print(msg_row, end="", flush=True)


class level(StrEnum):
	INFO = "INFO"
	WARNING = "WARNING"
	ERROR = "ERROR"
	DEBUG = "DEBUG"
