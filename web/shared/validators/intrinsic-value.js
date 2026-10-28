/**
 * Validate intrinsic value DCF inputs
 * @param {object} inputs - { growthDiscount, cashFlowDiscount, safetyMargin, projectionHorizon }
 * @returns {{ valid: boolean, errors: Record<string, string>, value: object }}
 */
export function validateIntrinsicValueInputs(inputs) {
	const {
		growthDiscount = 0,
		cashFlowDiscount = 0,
		safetyMargin = 0,
		projectionHorizon = 0,
	} = inputs

	const errors = {}

	// growthDiscount: 0–100, step 0.5
	if (String(growthDiscount).includes('+')) { errors.growthDiscount = 'Symbol + not allowed' }
	if (typeof growthDiscount !== 'number' || Number.isNaN(growthDiscount)) {
		errors.growthDiscount = 'Must be a number'
	} else if (growthDiscount < 0 || growthDiscount > 100) {
		errors.growthDiscount = 'Must be between 0 and 100'
	}

	// cashFlowDiscount: 0–100, step 0.5
	if (String(cashFlowDiscount).includes('+')) { errors.cashFlowDiscount = 'Symbol + not allowed' }
	if (typeof cashFlowDiscount !== 'number' || Number.isNaN(cashFlowDiscount)) {
		errors.cashFlowDiscount = 'Must be a number'
	} else if (cashFlowDiscount < 0 || cashFlowDiscount > 100) {
		errors.cashFlowDiscount = 'Must be between 0 and 100'
	}

	// safetyMargin: 0–100, step 1
	if (String(safetyMargin).includes('+')) { errors.safetyMargin = 'Symbol + not allowed' }
	if (typeof safetyMargin !== 'number' || Number.isNaN(safetyMargin)) {
		errors.safetyMargin = 'Must be a number'
	} else if (safetyMargin < 0 || safetyMargin > 100) {
		errors.safetyMargin = 'Must be between 0 and 100'
	}

	// projectionHorizon: integer, 1–100
	if (String(projectionHorizon).includes('+')) { errors.projectionHorizon = 'Symbol + not allowed' }
	if (!Number.isInteger(projectionHorizon) || projectionHorizon < 1 || projectionHorizon > 100) {
		errors.projectionHorizon = 'Must be an integer between 1 and 100'
	}

	if (Object.keys(errors).length > 0) {
		return { valid: false, errors, value: { growthDiscount, cashFlowDiscount, safetyMargin, projectionHorizon } }
	}

	const sanitized = {
		growthDiscount: Number.isFinite(growthDiscount) ? Number(growthDiscount) : 0,
		cashFlowDiscount: Number.isFinite(cashFlowDiscount) ? Number(cashFlowDiscount) : 0,
		safetyMargin: Number.isFinite(safetyMargin) ? Number(safetyMargin) : 0,
		projectionHorizon: Number.isInteger(projectionHorizon) ? Number(projectionHorizon) : 1,
	}

	return { valid: true, errors: {}, value: sanitized }
}
