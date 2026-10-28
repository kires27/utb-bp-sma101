/* DO NOT CHANGE FORMATTING !!! */

const FINANCIALS_SHAPE = {
	gross_margin: 				{ group: "profitability",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: true	},
	operating_margin: 			{ group: "profitability",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: false	},
	net_margin: 				{ group: "profitability",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: false	},
	return_on_equity: 			{ group: "profitability",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: false	},
	earning_per_share: 			{ group: "profitability",		isPercentage: false,	valueAboveMedianIsGood: true,	groupStart: false	},
	
	debt_to_equity: 			{ group: "financial stability",	isPercentage: false,	valueAboveMedianIsGood: false,	groupStart: true	},
	debt_growth: 				{ group: "financial stability",	isPercentage: true,		valueAboveMedianIsGood: false,	groupStart: false	},
	current_ratio: 				{ group: "financial stability",	isPercentage: false,	valueAboveMedianIsGood: true,	groupStart: false	},
	
	revenue_growth: 			{ group: "growth quality",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: true	},
	gross_income_growth: 		{ group: "growth quality",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: false	},
	net_income_growth: 			{ group: "growth quality",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: false	},
	retained_earning_growth: 	{ group: "growth quality",		isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: false	},
	revenues_per_share: 		{ group: "growth quality",		isPercentage: false,	valueAboveMedianIsGood: true,	groupStart: false	},
	
	capital_index: 				{ group: "capital discipline",	isPercentage: false,	valueAboveMedianIsGood: false,	groupStart: true	},
	payback_period: 			{ group: "capital discipline",	isPercentage: false,	valueAboveMedianIsGood: false,	groupStart: false	},
	
	assets_price: 				{ group: "market value",		isPercentage: false,	valueAboveMedianIsGood: true,	groupStart: true	},
	pe_ratio: 					{ group: "market value",		isPercentage: false,	valueAboveMedianIsGood: false,	groupStart: false	},
	pb_ratio: 					{ group: "market value",		isPercentage: false,	valueAboveMedianIsGood: false,	groupStart: false	},

	dividend_yield: 			{ group: "shareholder value",	isPercentage: true,		valueAboveMedianIsGood: true,	groupStart: true	},
}

export const FINANCIAL_GROUPS = ["profitability", "financial stability", "growth quality", "capital discipline", "market value", "shareholder value"]

export default FINANCIALS_SHAPE
