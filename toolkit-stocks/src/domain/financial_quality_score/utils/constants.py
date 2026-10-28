METRIC_COLUMNS = [
    "gross_margin", "operating_margin", "net_margin",
    "return_on_equity", "earnings_per_share",
    "debt_to_equity", "debt_growth", "current_ratio",
    "revenue_growth", "gross_income_growth", "net_income_growth",
    "retained_earning_growth", "revenues_per_share",
    "capital_index", "payback_period",
    "assets_price", "pe_ratio", "pb_ratio",
    "dividend_yield"
]

HIGHER_IS_BETTER = {
    "gross_margin": True,
    "operating_margin": True,
    "net_margin": True,
    "return_on_equity": True,
    "earnings_per_share": True,
    
    "debt_to_equity": False,
    "debt_growth": False,
    "current_ratio": True,
    
    "revenue_growth": True,
    "gross_income_growth": True,
    "net_income_growth": True,
    "retained_earning_growth": True,
    "revenues_per_share": True,
    
    "capital_index": False,
    "payback_period": False,
    
    "assets_price": True,
    "pe_ratio": False,
    "pb_ratio": False,
    
    "dividend_yield": True
}

GROUPS = {
    "profitability_earnings": {
        "weight": 0.25,
        "metrics": [
            "gross_margin", "operating_margin", "net_margin",
            "return_on_equity", "earnings_per_share"
        ]
    },
    "financial_stability": {
        "weight": 0.20,
        "metrics": ["debt_to_equity", "debt_growth", "current_ratio"]
    },
    "growth_quality": {
        "weight": 0.20,
        "metrics": [
            "revenue_growth", "gross_income_growth", "net_income_growth",
            "retained_earning_growth", "revenues_per_share"
        ]
    },
    "capital_discipline": {
        "weight": 0.10,
        "metrics": ["capital_index", "payback_period"]
    },
    "market_value": {
        "weight": 0.15,
        "metrics": ["assets_price", "pe_ratio", "pb_ratio"]
    },
    "shareholder_value": {
        "weight": 0.10,
        "metrics": ["dividend_yield"]
    }
}
