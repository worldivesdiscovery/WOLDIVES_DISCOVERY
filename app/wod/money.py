"""Amounts and currencies for Stripe (v50.45, encargo 2b · bloque 3, arreglo de las monedas sin decimales).

Stripe expects amounts in the smallest unit of each currency. Most currencies have 2 decimals (1 EUR = 100), but
some have none (1 JPY = 1, never × 100) and a few have 3 (1 KWD = 1000, last digit 0). Every conversion — charge,
deposit, refund, the check of the amount received and the yearly fee — goes through to_minor()/from_minor().
Source: Stripe documentation «Supported currencies», sections «Zero-decimal» and «Three-decimal».
"""
from __future__ import annotations

ZERO_DECIMAL = {'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 'MGA', 'PYG', 'RWF', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF'}
THREE_DECIMAL = {'BHD', 'JOD', 'KWD', 'OMR', 'TND'}
# Minimum amount Stripe accepts per currency (major units). Others: the equivalent of 0.50 USD, so 0.50 by default.
MINIMUM = {'EUR': 0.50, 'USD': 0.50, 'GBP': 0.30, 'MXN': 10, 'THB': 10, 'JPY': 50, 'AUD': 0.50, 'CAD': 0.50, 'CHF': 0.50,
           'NZD': 0.50, 'SGD': 0.50, 'HKD': 4.00, 'DKK': 2.50, 'NOK': 3.00, 'SEK': 3.00, 'PLN': 2.00, 'CZK': 15.00,
           'HUF': 175.00, 'RON': 2.00, 'BGN': 1.00, 'AED': 2.00, 'BRL': 0.50, 'INR': 0.50, 'MYR': 2.00}


def code(currency) -> str:
    c = str(currency or 'EUR').strip().upper()
    return c if len(c) == 3 and c.isalpha() else 'EUR'


def decimals(currency) -> int:
    c = code(currency)
    return 0 if c in ZERO_DECIMAL else (3 if c in THREE_DECIMAL else 2)


def to_minor(amount, currency) -> int:
    """12.5 EUR → 1250 · 5000 JPY → 5000 · 1.234 KWD → 1230 (Stripe asks the last digit to be 0)."""
    d = decimals(currency)
    n = int(round(float(amount or 0) * (10 ** d)))
    if d == 3: n = int(round(n / 10.0)) * 10
    return n


def from_minor(n, currency) -> float:
    d = decimals(currency)
    return round(int(n or 0) / (10 ** d), d)


def round_major(amount, currency) -> float:
    """An amount in the currency's own precision (a price in yen has no cents)."""
    return from_minor(to_minor(amount, currency), currency)


def minimum(currency) -> float:
    return MINIMUM.get(code(currency), 0.50 if decimals(currency) else 50)


def below_minimum(amount, currency) -> bool:
    return 0 < float(amount or 0) < minimum(currency)
