export const features = [
	{
		accentColor: "teal",
		title: "Financial Analysis",
		description:
			"Compare valuation, profitability, and growth metrics across thousands of companies.",
	},
	{
		accentColor: "purple",
		title: "Intrinsic Value",
		description:
			"Estimate fair value with DCF analysis and see how much a stock is truly worth.",
	},
	{
		accentColor: "gold",
		title: "Company Profile",
		description:
			"View real-time stock prices, market cap, and company fundamentals at a glance.",
	},
	{
		accentColor: "blue",
		title: "Smart Watchlist",
		description:
			"Build and manage watchlists with smart sorting, filtering, and real-time alerts.",
	}
];

export const floatCards = [
	{
		symbol: "AAPL",
		value: "+2.41%",
		up: true,
		dot: "var(--teal)",
		className: "float--1",
	},
	{
		symbol: "S&P 500",
		value: "5,234",
		up: true,
		dot: "var(--blue)",
		className: "float--2",
	},
	{
		symbol: "Portfolio",
		value: "+12.4k",
		up: true,
		dot: "var(--gold)",
		className: "float--3",
	},
	{
		symbol: "VIX",
		value: "13.42",
		up: false,
		dot: "var(--rose)",
		className: "float--4",
	},
];

export const plans = [
	{
		name: "Free",
		price: "€0",
		period: "/month",
		description: "Perfect for getting started",
		features: [
		],
		popular: false,
		buttonText: "Start Free",
	},
	{
		name: "Starter",
		price: "€5",
		period: "/month",
		description: "Great for individual investors",
		features: [
		],
		popular: false,
		buttonText: "Get Started",
	},
	{
		name: "Pro",
		price: "€15",
		period: "/month",
		description: "Best for active traders",
		features: [
		],
		popular: true,
		buttonText: "Go Pro",
	},
	{
		name: "Premium",
		price: "€30",
		period: "/month",
		description: "For serious investors",
		features: [
		],
		popular: false,
		buttonText: "Get Premium",
	},
];