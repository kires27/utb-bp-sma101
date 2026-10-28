
def normalize(values, higher_is_better=True):
    """
    values: list of (stock_id, value_or_None)
    Returns dict of {stock_id: score_0_to_100_or_None}
    """
    # 1. Filter out None values completely for the ranking pool
    valid_pairs = [(sid, v) for sid, v in values if v is not None]
    denom = len(valid_pairs) - 1

    # Base case: if 0 or 1 valid elements, assign a fallback score
    if denom <= 0:
        return {sid: (50.0 if v is not None else None) for sid, v in values}

    # 2. Extract and sort valid numbers
    valid_nums = [v for _, v in valid_pairs]
    # Higher is better -> sort descending; Lower is better -> sort ascending
    # This ensures the first occurrence index equals the count of "better" peers
    valid_nums.sort(reverse=higher_is_better)

    # 3. Build an efficient O(N) lookup for first-occurrence indexes (handles ties)
    rank_lookup = {}
    for idx, v in enumerate(valid_nums):
        if v not in rank_lookup:
            rank_lookup[v] = idx

    # 4. Map scores back to the original list, explicitly ignoring None values
    result = {}
    for sid, v in values:
        if v is None:
            result[sid] = None  # Outer loop skips this or writes None
        else:
            better_count = rank_lookup[v]
            result[sid] = round(100.0 - (better_count / denom) * 100.0, 2)

    return result
