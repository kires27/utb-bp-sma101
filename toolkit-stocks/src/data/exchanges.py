'''Static exchange seed: reference data for stock_exchange table.
Sessions are stable (last notable change: XIST 2024). Update manually.
exchange_code must match stock.exchange values exactly (yfinance names).'''

exchanges = [
	# --- Americas ---
	{"exchange_code": "NYSE", "mic": "XNYS", "short_name": "NYSE", "long_name": "New York Stock Exchange", "country": "United States", "timezone": "America/New_York", "open_time": "09:30", "close_time": "16:00", "currency": "USD"},
	{"exchange_code": "NasdaqGS", "mic": "XNAS", "short_name": "Nasdaq", "long_name": "Nasdaq Global Select Market", "country": "United States", "timezone": "America/New_York", "open_time": "09:30", "close_time": "16:00", "currency": "USD"},
	{"exchange_code": "NasdaqGM", "mic": "XNAS", "short_name": "Nasdaq", "long_name": "Nasdaq Global Market", "country": "United States", "timezone": "America/New_York", "open_time": "09:30", "close_time": "16:00", "currency": "USD"},
	{"exchange_code": "NasdaqCM", "mic": "XNAS", "short_name": "Nasdaq", "long_name": "Nasdaq Capital Market", "country": "United States", "timezone": "America/New_York", "open_time": "09:30", "close_time": "16:00", "currency": "USD"},
	{"exchange_code": "NYSEArca", "mic": "ARCX", "short_name": "NYSE Arca", "long_name": "NYSE Arca", "country": "United States", "timezone": "America/New_York", "open_time": "09:30", "close_time": "16:00", "currency": "USD"},
	{"exchange_code": "Toronto", "mic": "XTSE", "short_name": "TSX", "long_name": "Toronto Stock Exchange", "country": "Canada", "timezone": "America/Toronto", "open_time": "09:30", "close_time": "16:00", "currency": "CAD"},
	{"exchange_code": "São Paulo", "mic": "BVMF", "short_name": "B3", "long_name": "B3 - Brasil Bolsa Balcao", "country": "Brazil", "timezone": "America/Sao_Paulo", "open_time": "10:00", "close_time": "17:55", "currency": "BRL"},

	# --- Europe ---
	{"exchange_code": "LSE", "mic": "XLON", "short_name": "LSE", "long_name": "London Stock Exchange", "country": "United Kingdom", "timezone": "Europe/London", "open_time": "08:00", "close_time": "16:30", "currency": "GBp"},
	{"exchange_code": "XETRA", "mic": "XETR", "short_name": "XETRA", "long_name": "Deutsche Boerse XETRA", "country": "Germany", "timezone": "Europe/Berlin", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Paris", "mic": "XPAR", "short_name": "Euronext Paris", "long_name": "Euronext Paris", "country": "France", "timezone": "Europe/Paris", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Amsterdam", "mic": "XAMS", "short_name": "Euronext Amsterdam", "long_name": "Euronext Amsterdam", "country": "Netherlands", "timezone": "Europe/Amsterdam", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Brussels", "mic": "XBRU", "short_name": "Euronext Brussels", "long_name": "Euronext Brussels", "country": "Belgium", "timezone": "Europe/Brussels", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Lisbon", "mic": "XLIS", "short_name": "Euronext Lisbon", "long_name": "Euronext Lisbon", "country": "Portugal", "timezone": "Europe/Lisbon", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Milan", "mic": "XMIL", "short_name": "Borsa Italiana", "long_name": "Borsa Italiana (Euronext Milan)", "country": "Italy", "timezone": "Europe/Rome", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "MCE", "mic": "XMAD", "short_name": "BME", "long_name": "Bolsas y Mercados Espanoles", "country": "Spain", "timezone": "Europe/Madrid", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Swiss", "mic": "XSWX", "short_name": "SIX", "long_name": "SIX Swiss Exchange", "country": "Switzerland", "timezone": "Europe/Zurich", "open_time": "09:00", "close_time": "17:30", "currency": "CHF"},
	{"exchange_code": "Vienna", "mic": "XWBO", "short_name": "WBAG", "long_name": "Wiener Boerse", "country": "Austria", "timezone": "Europe/Vienna", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},
	{"exchange_code": "Warsaw", "mic": "XWAR", "short_name": "GPW", "long_name": "Warsaw Stock Exchange", "country": "Poland", "timezone": "Europe/Warsaw", "open_time": "09:00", "close_time": "17:00", "currency": "PLN"},
	{"exchange_code": "Oslo", "mic": "XOSL", "short_name": "Oslo Bors", "long_name": "Oslo Stock Exchange", "country": "Norway", "timezone": "Europe/Oslo", "open_time": "09:00", "close_time": "16:20", "currency": "NOK"},
	{"exchange_code": "Stockholm", "mic": "XSTO", "short_name": "Nasdaq Stockholm", "long_name": "Nasdaq Stockholm", "country": "Sweden", "timezone": "Europe/Stockholm", "open_time": "09:00", "close_time": "17:30", "currency": "SEK"},
	{"exchange_code": "Copenhagen", "mic": "XCSE", "short_name": "Nasdaq Copenhagen", "long_name": "Nasdaq Copenhagen", "country": "Denmark", "timezone": "Europe/Copenhagen", "open_time": "09:00", "close_time": "17:00", "currency": "DKK"},
	{"exchange_code": "Helsinki", "mic": "XHEL", "short_name": "Nasdaq Helsinki", "long_name": "Nasdaq Helsinki", "country": "Finland", "timezone": "Europe/Helsinki", "open_time": "09:00", "close_time": "17:30", "currency": "EUR"},

	# --- Asia-Pacific ---
	{"exchange_code": "Tokyo", "mic": "XTKS", "short_name": "TSE", "long_name": "Tokyo Stock Exchange", "country": "Japan", "timezone": "Asia/Tokyo", "open_time": "09:00", "close_time": "15:30", "currency": "JPY"},
	{"exchange_code": "Hong Kong", "mic": "XHKG", "short_name": "HKEX", "long_name": "Hong Kong Stock Exchange", "country": "Hong Kong", "timezone": "Asia/Hong_Kong", "open_time": "09:30", "close_time": "16:00", "currency": "HKD"},
	{"exchange_code": "HKSE", "mic": "XHKG", "short_name": "HKEX", "long_name": "Hong Kong Stock Exchange", "country": "Hong Kong", "timezone": "Asia/Hong_Kong", "open_time": "09:30", "close_time": "16:00", "currency": "HKD"},
	{"exchange_code": "Shanghai", "mic": "XSHG", "short_name": "SSE", "long_name": "Shanghai Stock Exchange", "country": "China", "timezone": "Asia/Shanghai", "open_time": "09:30", "close_time": "15:00", "currency": "CNY"},
	{"exchange_code": "Taiwan", "mic": "XTAI", "short_name": "TWSE", "long_name": "Taiwan Stock Exchange", "country": "Taiwan", "timezone": "Asia/Taipei", "open_time": "09:00", "close_time": "13:30", "currency": "TWD"},
	{"exchange_code": "KSE", "mic": "XKRX", "short_name": "KRX", "long_name": "Korea Exchange", "country": "South Korea", "timezone": "Asia/Seoul", "open_time": "09:00", "close_time": "15:30", "currency": "KRW"},
	{"exchange_code": "NSE", "mic": "XNSE", "short_name": "NSE", "long_name": "National Stock Exchange of India", "country": "India", "timezone": "Asia/Kolkata", "open_time": "09:15", "close_time": "15:30", "currency": "INR"},
	{"exchange_code": "BSE", "mic": "XBOM", "short_name": "BSE", "long_name": "Bombay Stock Exchange", "country": "India", "timezone": "Asia/Kolkata", "open_time": "09:15", "close_time": "15:30", "currency": "INR"},
	{"exchange_code": "ASX", "mic": "XASX", "short_name": "ASX", "long_name": "Australian Securities Exchange", "country": "Australia", "timezone": "Australia/Sydney", "open_time": "10:00", "close_time": "16:00", "currency": "AUD"},
	{"exchange_code": "SES", "mic": "XSES", "short_name": "SGX", "long_name": "Singapore Exchange", "country": "Singapore", "timezone": "Asia/Singapore", "open_time": "09:00", "close_time": "17:00", "currency": "SGD"},

	# --- Middle East ---
	{"exchange_code": "Istanbul", "mic": "XIST", "short_name": "BIST", "long_name": "Borsa Istanbul", "country": "Turkey", "timezone": "Europe/Istanbul", "open_time": "10:00", "close_time": "18:00", "currency": "TRY"},
	{"exchange_code": "TAI", "mic": "XTAE", "short_name": "TASE", "long_name": "Tel Aviv Stock Exchange", "country": "Israel", "timezone": "Asia/Jerusalem", "open_time": "09:59", "close_time": "17:14", "currency": "ILS"},
	{"exchange_code": "Doha", "mic": "XDSM", "short_name": "QSE", "long_name": "Qatar Stock Exchange", "country": "Qatar", "timezone": "Asia/Qatar", "open_time": "09:30", "close_time": "13:30", "currency": "QAR"},
	{"exchange_code": "Saudi", "mic": "XTAE", "short_name": "Tadawul", "long_name": "Saudi Stock Exchange (Tadawul)", "country": "Saudi Arabia", "timezone": "Asia/Riyadh", "open_time": "10:00", "close_time": "15:00", "currency": "SAR"},

	# --- Africa ---
	{"exchange_code": "JNB", "mic": "XJSE", "short_name": "JSE", "long_name": "Johannesburg Stock Exchange", "country": "South Africa", "timezone": "Africa/Johannesburg", "open_time": "09:00", "close_time": "17:00", "currency": "ZAR"},
]
