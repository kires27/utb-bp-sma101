from datetime import datetime


def get_period_type(period_type: str, ms_timestamp: int = 0) -> str | None:
    """
    Returns one of: 'Q1', 'Q2', 'Q3', 'Q4', 'FY', or 'TTM'

    :param period_type: raw periodType from yahooquery
    :param as_of_date: timestamp
    :returns: str | None
    """

    match(period_type.upper()):
        case "A":
            return "FY"
        case "Q":
            try:
                dt = datetime.fromtimestamp(ms_timestamp / 1000)
                month_number = dt.month

                if 1 <= month_number <= 3:
                    return "Q1"
                elif 4 <= month_number <= 6:
                    return "Q2"
                elif 7 <= month_number <= 9:
                    return "Q3"
                elif 10 <= month_number <= 12:
                    return "Q4"
            except Exception:
                return None
        case "TTM":
            return "TTM"

    return None
