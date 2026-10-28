import FINANCIALS_SHAPE, { FINANCIAL_GROUPS } from "./financial-analysis-shape.js"

const SymbolEntry = {
	symbol: 			{ group: null, isPercentage: false, valueAboveMedianIsGood: null, groupStart: true },
}
const qualityScoreEntry = {
	quality_score: 		{ group: null, isPercentage: false, valueAboveMedianIsGood: null, groupStart: true 	},
	intrinsic_value:	{ group: null, isPercentage: false, valueAboveMedianIsGood: null, groupStart: false },
	stock_price:		{ group: null, isPercentage: false, valueAboveMedianIsGood: null, groupStart: false }
}

export const WATCHLIST_SHAPE = { ...SymbolEntry, ...FINANCIALS_SHAPE, ...qualityScoreEntry }
export const WATCHLIST_GROUPS = [null, ...FINANCIAL_GROUPS, null]

