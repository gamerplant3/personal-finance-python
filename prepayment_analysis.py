"""CLI wrapper for mortgage prepayment scenario tables."""

from mortgage_math import (
    DEFAULT_AMORTIZATION_YEARS,
    DEFAULT_ANNUAL_RATE,
    DEFAULT_PREPAYMENT_EXTRAS,
    DEFAULT_PRINCIPAL,
    DEFAULT_TERM_YEARS,
    prepayment_scenarios,
)

principal = DEFAULT_PRINCIPAL
annual_rate = DEFAULT_ANNUAL_RATE
years = DEFAULT_AMORTIZATION_YEARS
term_years = DEFAULT_TERM_YEARS
extras = list(DEFAULT_PREPAYMENT_EXTRAS)

df_m, df_a, meta = prepayment_scenarios(principal, annual_rate, years, term_years, extras)

print(f"--- TABLE 1: MONTHLY PAYMENTS OVER {term_years} YRS (${meta['monthly_payment']:,.2f}) ---")
print(df_m.to_string(index=False))
print(f"\n--- TABLE 2: ACCELERATED WEEKLY PAYMENTS OVER {term_years} YRS "
      f"(${meta['accelerated_weekly_payment']:,.2f}) ---")
print(df_a.to_string(index=False))
