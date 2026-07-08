const CACHE_KEY = "currency-rates-cache";
const DEFAULT_BASE_CURRENCY = "SGD";

function normalizeCurrencyCode(currencyCode) {
    if (!currencyCode) {
        return DEFAULT_BASE_CURRENCY;
    }

    const cleaned = String(currencyCode).trim().toUpperCase();
    const mapping = {
        RM: "MYR",
        "S$": "SGD",
        SGD: "SGD",
        MYR: "MYR",
        USD: "USD",
    };

    return mapping[cleaned] || cleaned;
}

function readRateCache() {
    try {
        const raw = localStorage.getItem(CACHE_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch {
        return {};
    }
}

function writeRateCache(rateCache) {
    localStorage.setItem(CACHE_KEY, JSON.stringify(rateCache));
}

async function getExchangeRate(fromCurrency, toCurrency = DEFAULT_BASE_CURRENCY) {
    const sourceCurrency = normalizeCurrencyCode(fromCurrency);
    const targetCurrency = normalizeCurrencyCode(toCurrency);

    if (sourceCurrency === targetCurrency) {
        return 1;
    }

    const cachedRates = readRateCache();
    const cacheKey = `${sourceCurrency}-${targetCurrency}`;
    if (cachedRates[cacheKey]) {
        return cachedRates[cacheKey];
    }

    try {
        const response = await fetch("https://open.er-api.com/v6/latest/SGD");
        if (!response.ok) {
            return null;
        }

        const payload = await response.json();
        const rates = payload?.rates || {};
        const sourceToSgd = sourceCurrency === "SGD" ? 1 : (1 / Number(rates[sourceCurrency] || 0));
        const targetToSgd = targetCurrency === "SGD" ? 1 : Number(rates[targetCurrency] || 0);
        const rate = sourceToSgd * targetToSgd;

        if (Number.isFinite(rate) && rate > 0) {
            cachedRates[cacheKey] = rate;
            writeRateCache(cachedRates);
            return rate;
        }
    } catch {
        return cachedRates[cacheKey] || null;
    }

    return cachedRates[cacheKey] || null;
}

export async function convertAmountToSgd(amount, currencyCode) {
    const numericAmount = Number(amount);
    if (!Number.isFinite(numericAmount)) {
        return null;
    }

    const normalizedCurrency = normalizeCurrencyCode(currencyCode);
    if (normalizedCurrency === DEFAULT_BASE_CURRENCY) {
        return numericAmount;
    }

    const rate = await getExchangeRate(normalizedCurrency, DEFAULT_BASE_CURRENCY);
    if (!rate) {
        return null;
    }

    return numericAmount * rate;
}

export { normalizeCurrencyCode };
