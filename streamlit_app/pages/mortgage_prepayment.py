"""Mortgage prepayment scenario analysis."""

import streamlit as st
from mortgage_math import (
    DEFAULT_PREPAYMENT_EXTRAS,
    balance_at_maturity,
    calculate_term_stats,
    monthly_payment,
    prepayment_scenarios,
)
from streamlit_app.components.charts import (
    prepayment_balance_comparison,
    prepayment_interest_saved_comparison,
)
from streamlit_app.components.mortgage_profile import profile_weekly_payment, render_mortgage_editor

def render():
    st.title("Mortgage Prepayment Analysis")
    m = render_mortgage_editor()
    principal = float(m["principal"])
    annual_rate = float(m["annual_rate"])
    years = int(m["amortization_years"])
    term_years = int(m["term_years"])
    if "mp_extras" not in st.session_state:
        st.session_state.mp_extras = ",".join(str(int(x)) for x in DEFAULT_PREPAYMENT_EXTRAS)
    extras_text = st.sidebar.text_input(
        "Extra weekly amounts (comma-separated)", key="mp_extras",
    )
    extras = [float(x.strip()) for x in extras_text.split(",") if x.strip()]
    weekly_extra = float(m["extra_weekly"])
    monthly_pmt = monthly_payment(principal, annual_rate, years)
    acc_pmt = profile_weekly_payment(m)
    mat_result = balance_at_maturity(
        principal, annual_rate, acc_pmt, m["maturity_date"], m["next_payment_date"],
    )
    _, total_int, _ = calculate_term_stats(
        principal, annual_rate, term_years, acc_pmt, weekly_extra, "weekly",
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly Payment", f"${monthly_pmt:,.2f}")
    c2.metric("Accelerated Weekly", f"${acc_pmt:,.2f}", help="Monthly payment ÷ 4 (52 payments/yr)")
    c3.metric("Balance at maturity", f"${mat_result.balance_at_maturity:,.2f}")
    c4.metric("Interest over term", f"${total_int:,.2f}", help=f"Total interest over {term_years}-year term")
    df_m, df_a, meta = prepayment_scenarios(
        principal, annual_rate, years, term_years, extras, accelerated_weekly=acc_pmt,
    )
    st.markdown(f"**Monthly payments over {term_years} years** (${monthly_pmt:,.2f})")
    st.caption(
        "Sidebar extras are weekly amounts. Monthly table shows weekly × 4 per month "
        "(same convention as accelerated weekly = monthly ÷ 4)."
    )
    st.dataframe(df_m, width="stretch", hide_index=True)
    st.markdown(f"**Accelerated weekly over {term_years} years** (${acc_pmt:,.2f})")
    st.dataframe(df_a, width="stretch", hide_index=True)
    st.info(f"Frequency savings vs monthly baseline: ${meta['saved_by_frequency']:,.2f}")
    st.plotly_chart(
        prepayment_balance_comparison(extras, meta["monthly_balances"], meta["acc_balances"]),
        width="stretch",
        key="prepayment_balance_comparison",
    )
    st.plotly_chart(
        prepayment_interest_saved_comparison(
            extras, meta["monthly_interest_saved"], meta["acc_total_saved"],
        ),
        width="stretch",
        key="prepayment_interest_comparison",
    )
