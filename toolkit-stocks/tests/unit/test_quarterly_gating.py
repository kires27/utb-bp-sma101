'''Quarterly fetch gating: quarterly_fetch_decision boundary + suppression cases.

Mirrors the SQL in lib.supabase.sql_functions.get_quarterly_fetch_ids.
Fetch iff (swept AND gap known AND gap <= sweep window) OR (stale AND NOT suppressed).
'''
from pipeline.statements import quarterly_fetch_decision

WINDOW = 95
LOOKAHEAD = 7
MAX_GAP = 180
SWEEP = 180


def test_gap_boundary():
	# stale when gap > 95
	assert quarterly_fetch_decision(94, None) is False	# fresh
	assert quarterly_fetch_decision(WINDOW, None) is False	# boundary = fresh
	assert quarterly_fetch_decision(96, None) is True	# stale, no event -> fetch


def test_unknown_gap_fetches():
	# no rows at all (None) -> COALESCE fallback -> maximally stale -> fetch
	assert quarterly_fetch_decision(None, None) is True
	# unknown gap suppresses nothing, even with a far event
	assert quarterly_fetch_decision(None, 400) is True


def test_no_event_fallback():
	# stale, no calendar coverage (non-US / sweep miss) -> gap trigger
	assert quarterly_fetch_decision(100, None) is True
	assert quarterly_fetch_decision(500, None) is True


def test_far_future_event_suppresses():
	assert quarterly_fetch_decision(100, 30) is False
	assert quarterly_fetch_decision(120, 400) is False


def test_event_within_lookahead_fetches():
	# event <= 7d out (or just passed): fetch daily until fresh
	assert quarterly_fetch_decision(100, LOOKAHEAD) is True
	assert quarterly_fetch_decision(100, 1) is True
	assert quarterly_fetch_decision(100, 0) is True


def test_postponed_event_suppression_drops():
	# event rescheduled into the near term -> suppression drops -> fetch
	assert quarterly_fetch_decision(120, 90) is False	# still far-future
	assert quarterly_fetch_decision(120, 5) is True	# now inside lookahead


def test_gap_too_old_never_suppressed():
	# suppression ignored once gap >= 180 (data missing >~2 quarters)
	assert quarterly_fetch_decision(MAX_GAP, 400) is True
	assert quarterly_fetch_decision(365, 400) is True
	assert quarterly_fetch_decision(MAX_GAP - 1, 400) is False	# still suppressable


def test_boundary_combinations():
	# stale + event exactly at lookahead edge -> fetch (strictly-beyond rule)
	assert quarterly_fetch_decision(96, LOOKAHEAD + 1) is False	# 8d out -> suppress
	assert quarterly_fetch_decision(96, LOOKAHEAD) is True	# 7d out -> fetch
	# fresh gap suppresses nothing regardless
	assert quarterly_fetch_decision(10, 400) is False


def test_sweep_overrides_fresh_window():
	# sweep shard catches restatements of recent data the fresh window misses
	assert quarterly_fetch_decision(10, None, swept=True) is True
	assert quarterly_fetch_decision(WINDOW, None, swept=True) is True


def test_sweep_overrides_suppression():
	# sweep ignores the earnings calendar entirely (no signal for revisions)
	assert quarterly_fetch_decision(100, 400, swept=True) is True
	assert quarterly_fetch_decision(120, 30, swept=True) is True


def test_sweep_window_boundary():
	# sweep applies only to known rows within the sweep window
	assert quarterly_fetch_decision(SWEEP, 400, swept=True) is True
	assert quarterly_fetch_decision(SWEEP + 1, 400, swept=True) is True	# beyond window -> normal rules (gap >= 180 -> never suppressed)
	assert quarterly_fetch_decision(None, None, swept=True) is True	# unknown gap -> stale branch fetches
	# not swept -> behavior unchanged
	assert quarterly_fetch_decision(10, None, swept=False) is False
	assert quarterly_fetch_decision(10, 400, swept=False) is False
