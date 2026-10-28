import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
	'''Load a frozen API payload from tests/fixtures/<name>.json.'''
	with open(FIXTURES_DIR / f"{name}.json", encoding="utf-8") as fh:
		return json.load(fh)


def expected_path(path: Path) -> Path:
	'''Sibling *.expected.json path for a fixture file.'''
	return path.with_name(path.stem + ".expected.json")
