"""
Canadian mortgage math with semi-annual compounding.
Canadian mortgage math shared by CLI scripts and Streamlit.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal
import pandas as pd

# --- Default mortgage scenario (shared by CLI, Streamlit, tests) ---

DEFAULT_PRINCIPAL = 350_000.0
DEFAULT_ANNUAL_RATE = 0.037
DEFAULT_AMORTIZATION_YEARS = 25
DEFAULT_TERM_YEARS = 5
DEFAULT_EXTRA_WEEKLY = 0.0
DEFAULT_PREPAYMENT_EXTRAS: list[float] = [0, 100, 150, 200, 250]


def default_mortgage_scenario() -> dict[str, float | int]:
    """Core mortgage numbers without date fields."""
    return {
        "principal": DEFAULT_PRINCIPAL,
        "annual_rate": DEFAULT_ANNUAL_RATE,
        "amortization_years": DEFAULT_AMORTIZATION_YEARS,
        "term_years": DEFAULT_TERM_YEARS,
        "extra_weekly": DEFAULT_EXTRA_WEEKLY,
    }


# --- Rate conversions (semi-annual compounding) ---

def monthly_rate(annual_rate: float) -> float:
    i_sa = annual_rate / 2
    return (1 + i_sa) ** (2 / 12) - 1

def weekly_rate(annual_rate: float) -> float:
    i_sa = annual_rate / 2
    return (1 + i_sa) ** (2 / 52) - 1

def daily_rate(annual_rate: float) -> float:
    i_sa = annual_rate / 2
    return (1 + i_sa) ** (2 / 365) - 1

def monthly_payment(principal: float, annual_rate: float, years: float | int) -> float:
    years = int(years)
    i_m = monthly_rate(annual_rate)
    return round(principal * (i_m / (1 - (1 + i_m) ** (-years * 12))), 2)

def accelerated_weekly_payment(principal: float, annual_rate: float, years: float | int) -> float:
    return round(monthly_payment(principal, annual_rate, years) / 4, 2)

# --- Balance at maturity (stub period) ---

@dataclass

class MaturityResult:
    principal_after_last_payment: float
    accrued_interest: float
    balance_at_maturity: float
    last_payment_date: date

def balance_at_maturity(
    principal: float,
    annual_rate: float,
    payment: float,
    maturity_date: date,
    next_payment_date: date,
) -> MaturityResult:
    """Project weekly payments until maturity, including stub-period interest."""
    i_w = weekly_rate(annual_rate)
    i_d = daily_rate(annual_rate)
    balance = principal
    current = next_payment_date
    last_pmt = next_payment_date
    while current <= maturity_date:
        interest_charge = balance * i_w
        balance -= payment - interest_charge
        last_pmt = current
        current += timedelta(days=7)

    days_stub = (maturity_date - last_pmt).days
    accrued = balance * ((1 + i_d) ** days_stub - 1) if days_stub > 0 else 0.0
    return MaturityResult(
        principal_after_last_payment=round(balance, 2),
        accrued_interest=round(accrued, 2),
        balance_at_maturity=round(balance + accrued, 2),
        last_payment_date=last_pmt,
    )

# --- Term prepayment scenarios (from prepayment_analysis.py) ---

def calculate_term_stats(
    principal: float,
    annual_rate: float,
    term_years: float | int,
    base_payment: float,
    weekly_extra: float = 0.0,
    frequency: Literal["weekly", "monthly"] = "weekly",
) -> tuple[float, float, float]:
    """Return (principal_paid, total_interest, ending_balance) over the term."""
    term_years = int(term_years)
    balance = principal
    total_interest = 0.0
    total_principal_paid = 0.0
    i_m = monthly_rate(annual_rate)
    i_w = weekly_rate(annual_rate)
    if frequency == "monthly":
        for _ in range(term_years * 12):
            interest_charge = balance * i_m
            extra = weekly_extra * (52 / 12)
            principal_reduction = (base_payment - interest_charge) + extra
            balance -= principal_reduction
            total_interest += interest_charge
            total_principal_paid += principal_reduction
    else:
        for _ in range(term_years * 52):
            interest_charge = balance * i_w
            principal_reduction = (base_payment + weekly_extra) - interest_charge
            balance -= principal_reduction
            total_interest += interest_charge
            total_principal_paid += principal_reduction

    return round(total_principal_paid, 2), round(total_interest, 2), round(balance, 2)

def prepayment_scenarios(
    principal: float,
    annual_rate: float,
    years: float | int,
    term_years: float | int,
    extras: list[float] | None = None,
    accelerated_weekly: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Build monthly and accelerated-weekly prepayment comparison tables."""
    years = int(years)
    term_years = int(term_years)
    extras = extras or list(DEFAULT_PREPAYMENT_EXTRAS)
    monthly_pmt = monthly_payment(principal, annual_rate, years)
    acc_weekly_pmt = accelerated_weekly if accelerated_weekly is not None else accelerated_weekly_payment(
        principal, annual_rate, years,
    )
    baseline_int_m = calculate_term_stats(principal, annual_rate, term_years, monthly_pmt, 0, "monthly")[1]
    baseline_int_acc = calculate_term_stats(
        principal, annual_rate, term_years, acc_weekly_pmt, 0, "weekly",
    )[1]
    saved_by_freq = round(baseline_int_m - baseline_int_acc, 2)
    monthly_balances: list[float] = []
    monthly_interest_saved: list[float] = []
    monthly_rows = []
    for e in extras:
        # Simulation uses weekly × 52/12 per month; table displays weekly × 4.
        monthly_extra_display = e * 4
        total_principal, total_interest, bal = calculate_term_stats(
            principal, annual_rate, term_years, monthly_pmt, e, "monthly",
        )
        interest_saved = baseline_int_m - total_interest
        monthly_balances.append(bal)
        monthly_interest_saved.append(interest_saved)
        monthly_rows.append({
            "Extra": f"${monthly_extra_display:,.2f}",
            "Prepayments": f"${monthly_extra_display * 12 * term_years:,.2f}",
            "Principal Paid": f"${total_principal:,.2f}",
            "Interest Saved": f"${interest_saved:,.2f}",
            "Balance at Renewal": f"${bal:,.2f}",
        })

    acc_balances: list[float] = []
    acc_total_saved: list[float] = []
    acc_rows = []
    for e in extras:
        total_principal, total_interest, bal = calculate_term_stats(
            principal, annual_rate, term_years, acc_weekly_pmt, e, "weekly",
        )
        prepay_saved = baseline_int_acc - total_interest
        total_saved = baseline_int_m - total_interest
        acc_balances.append(bal)
        acc_total_saved.append(total_saved)
        acc_rows.append({
            "Extra": f"${e:,.0f}",
            "Prepayments": f"${e * 52 * term_years:,.2f}",
            "Principal Paid": f"${total_principal:,.2f}",
            "Saved by Prepay": f"${prepay_saved:,.2f}",
            "Total Int Saved": f"${total_saved:,.2f}",
            "Balance at Renewal": f"${bal:,.2f}",
        })

    meta = {
        "monthly_payment": monthly_pmt,
        "accelerated_weekly_payment": acc_weekly_pmt,
        "saved_by_frequency": saved_by_freq,
        "extras": extras,
        "monthly_balances": monthly_balances,
        "acc_balances": acc_balances,
        "monthly_interest_saved": monthly_interest_saved,
        "acc_total_saved": acc_total_saved,
    }
    return pd.DataFrame(monthly_rows), pd.DataFrame(acc_rows), meta

# --- CLI entry ---

if __name__ == "__main__":
    payment = accelerated_weekly_payment(
        DEFAULT_PRINCIPAL, DEFAULT_ANNUAL_RATE, DEFAULT_AMORTIZATION_YEARS,
    )
    result = balance_at_maturity(
        principal=DEFAULT_PRINCIPAL,
        annual_rate=DEFAULT_ANNUAL_RATE,
        payment=payment,
        maturity_date=date(2026, 4, 1),
        next_payment_date=date(2026, 1, 15),
    )
    print(f"Principal after last payment (Mar 26): ${result.principal_after_last_payment:,.2f}")
    print(f"Accrued interest (6 days till maturity): ${result.accrued_interest:,.2f}")
    print(f"Balance at Maturity (Apr 1): ${result.balance_at_maturity:,.2f}")
