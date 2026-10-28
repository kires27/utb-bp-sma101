import { roundAnyNumber } from "#shared/functions/numeric";

function calculateNetIncome(income, dividends, shares) {
	const div = dividends || 0;
	return (income - div) / shares + 1;
}


/**
 * intrinsic value without margin of safety.
 * returns dictionary with analysis.
 * @param {number} price newest (closing) price
 * @param {number} marketCap newest
 * @param {number} cashAndEquivalents from newest balance sheet
 * @param {number} shareIssued from newest balance sheet
 * @param {object[]} cashFlow list of statements (newest first)
 * @param {number} growthRateDiscount growth rate
 * @param {number} futureDiscountRate Discount for future free cash flow and terminal value.
 * @returns {object}
 */
export default function calculateIntrinsicValue(
	marketCap,
	stockPrice,
	cashAndEquivalents,
	shareIssued,
	cashFlow,
	growthRateDiscount,
	futureDiscountRate,
	safetyMargin,
) {
	const grdDecimal = 1 - growthRateDiscount / 100;
	const fdrDecimal = 1 + futureDiscountRate / 100;
	const smDecimal = 1 - safetyMargin / 100

	/** list of dates */
	// const dates = cashFlow.map((item) => item["fiscal_date"].split("-")[0]);

	/** free cash flows from newest to oldest */
	const { dates, values: fcfs } = freeCashFlows(cashFlow);
	const projection = fcfs.length;

	const agr = annualGrowthRate(fcfs);
	const dagr = agr * grdDecimal;

	const nfcf = normalizedFreeCashFlow(fcfs);
	const ffcfs = futureFreeCashFlows(nfcf, projection, dagr);

	const pfcf = priceToFreeCashFlow(marketCap, fcfs[0]);
	const ter = ffcfs.at(-1) * pfcf;

	const dffcfs = discountedFutureFreeCashFlows(ffcfs, projection, fdrDecimal);
	const dffcfSum = dffcfs.reduce((acc, v) => acc + v, 0);
	const dter = ter / (fdrDecimal ** projection);
	const pv = dffcfSum + dter;

	const iv = pv + cashAndEquivalents;

	const ivps = (iv * smDecimal) / shareIssued;
	// intrinsic value per share percentage difference
	const ivpspd = ((ivps - stockPrice) / stockPrice) * 100

	return {
		"stock_price": stockPrice,
		"market_cap": [
			marketCap,
			roundAnyNumber(marketCap, 2)
		],
		"projection_horizon": projection,
		"annual_growth_rate": [
			agr * 100,
			roundAnyNumber(agr * 100, 1)
		],
		// "free_cash_flows": Object.fromEntries(
		// 	fcfs.map((val, i) => [dates[i], val])
		// ),
		// "future_free_cash_flows": ffcfs.reduce((acc, val, i) => {
		// 	acc[Number(dates[0]) + i + 1] = val;
		// 	return acc;
		// }, {}),
		// "discounted_future_free_cash_flows": dffcfs.reduce(
		// 	(acc, val, i) => {
		// 		acc[Number(dates[0]) + i + 1] = val;
		// 		return acc;
		// 	}, {}),
		"intrinsic_value": [
			iv,
			roundAnyNumber(iv, 2)
		],
		"intrinsic_value_per_share": [
			ivps,
			roundAnyNumber(ivps, 2)
		],
		"iv_upside": [
			ivpspd,
			`${ivpspd >= 0 ? "+" : ""}${roundAnyNumber(ivpspd, 1)}%`
		]
	};
}

/**
 * list of free cash flows, starting from newest
 * @param {object[]} cashFlow
 * @param {number} index
 * @param {{dates: string[], values: number[]}} holder
 * @returns {{dates: string[], values: number[]}}
 */
function freeCashFlows(cashFlow, index = 0, holder = { dates: [], values: [] }) {
	if (index >= cashFlow.length) return holder;

	// check if statements are from newest to oldest
	const date = (i) => cashFlow[i]["fiscal_date"];

	if (index + 1 < cashFlow.length &&
		date(index) <= date(index + 1)
	) {
		throw createError({ statusCode: 400, statusMessage: 'Cash Flow statements corrupted' })
	};

	const value = cashFlow[index]["free_cash_flow"];

	if (typeof value === "number" && !isNaN(value)) {
		holder.dates.push(date(index));
		holder.values.push(value);
	}

	return freeCashFlows(cashFlow, index + 1, holder);
};


/**
 * @param {number[]} fcfs
 * @returns {number}
 */
function annualGrowthRate(fcfs) {
	const periods = fcfs.length;
	const first = fcfs[0];
	const last = fcfs.at(-1);

	// negative/zero → no growth projection, conservative 0
	if (last === 0 || first / last < 0) return 0.0001; 

	return (first / last) ** (1 / periods) - 1;
};

/**
 * @param {number[]} fcfs
 * @returns {number}
 */
function normalizedFreeCashFlow(fcfs) {
	const sum = fcfs.reduce((acc, v) => acc + v, 0);
	return sum / fcfs.length;
}

/**
 * @param {number} fcf normalized free cash flow
 * @param {number} lfcfs length of the fcf array
 * @param {number} dagr discounted annual growth rate of fcf
 * @param {number[]} holder hold values in array to return
 * @returns {number[]}
 */
function futureFreeCashFlows(fcf, lfcfs, dagr, holder = []) {
	if (lfcfs <= 0) return holder;

	const dfcf = fcf * (1 + dagr);
	return futureFreeCashFlows(
		dfcf,
		lfcfs - 1,
		dagr,
		[...holder, dfcf]
	);
}

/**
 * TODO FCF newest value - must be average across industry
 * @param {number} marketCap market cap
 * @param {number} fcf newest free cash flow
 */
function priceToFreeCashFlow(marketCap, fcf) {
	return marketCap / fcf;
};

/**
 * @param {number[]} ffcfs future free cash flows
 * @param {number} length length of ffcfs
 * @param {number} disc discount
 * @param {number} exp exponent + also works as an index
 * @param {number[]} holder
 * @returns {number[]}
 */
function discountedFutureFreeCashFlows(
	ffcfs,
	length,
	disc,
	exp = 1,
	holder = []
) {
	if (length <= 0) return holder;

	const index = exp - 1;
	return discountedFutureFreeCashFlows(
		ffcfs,
		length - 1,
		disc,
		exp + 1,
		[...holder, ffcfs[index] / disc ** exp]
	);
};
