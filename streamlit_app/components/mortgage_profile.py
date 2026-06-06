"""Shared mortgage parameters stored in session state.

The Mortgage Prepayment page is the single place to edit these values.
Other dashboard pages read from this profile.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from mortgage_math import (
    DEFAULT_AMORTIZATION_YEARS,
    DEFAULT_ANNUAL_RATE,
    DEFAULT_EXTRA_WEEKLY,
    DEFAULT_PRINCIPAL,
    DEFAULT_TERM_YEARS,
    accelerated_weekly_payment,
)


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _fresh_mortgage_defaults() -> dict:
    today = date.today()
    term = DEFAULT_TERM_YEARS
    return {
        "principal": DEFAULT_PRINCIPAL,
        "annual_rate": DEFAULT_ANNUAL_RATE,
        "amortization_years": DEFAULT_AMORTIZATION_YEARS,
        "term_years": term,
        "extra_weekly": DEFAULT_EXTRA_WEEKLY,
        "maturity_date": _add_years(today, term),
        "next_payment_date": today + timedelta(days=7),
        "payment_weekday": 3,
    }


def init_mortgage_profile() -> None:
    if "mortgage" not in st.session_state:
        st.session_state.mortgage = _fresh_mortgage_defaults()


def get_mortgage_profile() -> dict:
    init_mortgage_profile()
    profile = st.session_state.mortgage
    profile.pop("weekly_payment", None)
    profile.pop("amortizing_enabled", None)
    return profile


def profile_weekly_payment(m: dict | None = None) -> float:
    """Accelerated weekly payment (monthly payment / 4)."""
    profile = m or get_mortgage_profile()
    return accelerated_weekly_payment(
        float(profile["principal"]),
        float(profile["annual_rate"]),
        int(profile["amortization_years"]),
    )


def _seed_mortgage_widgets(m: dict) -> None:
    """Initialize widget keys once so value= does not reset user edits on reruns."""
    if "mp_principal" not in st.session_state:
        st.session_state.mp_principal = float(m["principal"])
    if "mp_rate" not in st.session_state:
        st.session_state.mp_rate = float(m["annual_rate"] * 100)
    if "mp_amort" not in st.session_state:
        st.session_state.mp_amort = float(m["amortization_years"])
    if "mp_term" not in st.session_state:
        st.session_state.mp_term = float(m["term_years"])
    if "mp_extra" not in st.session_state:
        st.session_state.mp_extra = float(m["extra_weekly"])
    if "mp_maturity" not in st.session_state:
        st.session_state.mp_maturity = m.get(
            "maturity_date", _add_years(date.today(), int(m.get("term_years", DEFAULT_TERM_YEARS))),
        )
    if "mp_next_pmt" not in st.session_state:
        st.session_state.mp_next_pmt = m.get("next_payment_date", date.today() + timedelta(days=7))


def _apply_mortgage_widgets(m: dict) -> dict:
    m["principal"] = float(st.session_state.mp_principal)
    m["annual_rate"] = float(st.session_state.mp_rate) / 100
    m["amortization_years"] = float(st.session_state.mp_amort)
    m["term_years"] = float(st.session_state.mp_term)
    m["extra_weekly"] = float(st.session_state.mp_extra)
    m["maturity_date"] = st.session_state.mp_maturity
    m["next_payment_date"] = st.session_state.mp_next_pmt
    return m


def render_mortgage_editor() -> dict:
    """Full mortgage sidebar editor (Mortgage Prepayment page only)."""
    m = get_mortgage_profile()
    _seed_mortgage_widgets(m)
    with st.sidebar:
        st.subheader("Mortgage Parameters")
        st.caption("These values are shared across Cashflow and other pages.")
        st.number_input("Principal / balance ($)", step=1000.0, key="mp_principal")
        st.number_input("Annual rate %", step=0.01, key="mp_rate")
        st.number_input(
            "Amortization (years)", min_value=1.0, step=1.0, key="mp_amort",
        )
        saved_term = int(m.get("_saved_term_years", m.get("term_years", DEFAULT_TERM_YEARS)))
        st.number_input("Term (years)", min_value=1.0, step=1.0, key="mp_term")
        new_term = int(st.session_state.mp_term)
        if new_term != saved_term:
            st.session_state.mp_maturity = _add_years(date.today(), new_term)
        m["_saved_term_years"] = new_term
        st.number_input("Extra weekly prepay ($)", step=50.0, key="mp_extra")
        st.divider()
        st.subheader("Current Term Dates")
        st.date_input("Maturity date", key="mp_maturity")
        st.date_input("Next payment date", key="mp_next_pmt")

    m = _apply_mortgage_widgets(m)
    st.session_state.mortgage = m
    return m


def show_mortgage_sidebar_summary() -> None:
    """Read-only mortgage summary for pages that consume the shared profile."""
    m = get_mortgage_profile()
    weekly_pmt = profile_weekly_payment(m)
    with st.sidebar:
        st.subheader("Mortgage")
        st.caption("Edit on **Mortgage Prepayment** page.")
        st.markdown(
            f"- Principal: **${m['principal']:,.2f}**  \n"
            f"- Rate: **{m['annual_rate'] * 100:.2f}%**  \n"
            f"- Amortization: **{int(m['amortization_years'])} yr**  \n"
            f"- Term: **{int(m['term_years'])} yr**  \n"
            f"- Accelerated weekly: **${weekly_pmt:,.2f}**"
        )
