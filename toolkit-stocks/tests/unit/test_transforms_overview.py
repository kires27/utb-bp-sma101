import json

from lib.transforms.overview import build_overview_row


def _row(**overrides):
	profile = {
		"address1": "1 Infinite Loop",
		"longBusinessSummary": "Phones",
		"fullTimeEmployees": 160000,
		"industry": "Consumer Electronics",
		"sector": "Technology",
		"companyOfficers": [{"name": "Tim"}],
		"phone": "123",
		"website": "apple.com",
		"city": "Cupertino",
		"country": "US",
		"zip": "95014",
		"longName": "Apple Inc.",
		"fullExchangeName": "NMS",
		"currency": "USD",
	}
	profile.update(overrides)
	return build_overview_row("AAPL", profile, None, {}, None)


def test_yf_snake_case_shape():
	row = _row()
	assert row["address"] == "1 Infinite Loop"
	assert row["description"] == "Phones"
	assert row["employees"] == 160000
	assert row["phone_number"] == "123"
	assert row["website"] == "apple.com"


def test_sector_industry_swapped_on_purpose():
	row = _row()
	assert row["sector"] == "Consumer Electronics"	# profile.industry
	assert row["industry"] == "Technology"	# profile.sector


def test_db_meta_wins_over_profile():
	row = build_overview_row(
		"AAPL", {}, [], {"name": "Old Name", "exchange": "OLD", "currency": "EUR"}, None
	)
	assert row["name"] == "Old Name"
	assert row["exchange"] == "OLD"
	assert row["currency"] == "EUR"


def test_yf_info_fallback_when_profile_and_db_empty():
	row = build_overview_row(
		"AAPL", {}, [], {},
		{"longName": "Apple Inc.", "fullExchangeName": "NMS", "currency": "USD"},
	)
	assert row["name"] == "Apple Inc."
	assert row["exchange"] == "NMS"
	assert row["currency"] == "USD"


def test_officers_fallback_chain():
	# officers arg None -> profile.companyOfficers
	row = _row()
	assert json.loads(row["key_executives"]) == [{"name": "Tim"}]
	# none anywhere -> empty list
	row2 = build_overview_row("AAPL", {}, None, {}, None)
	assert json.loads(row2["key_executives"]) == []


def test_omitted_name_keys_not_in_row():
	row = build_overview_row("AAPL", {}, [], {}, None)
	assert "name" not in row
	assert "exchange" not in row
	assert "currency" not in row


def test_error_returns_empty_dict():
	assert build_overview_row("AAPL", None, None, {}, None) == {}
