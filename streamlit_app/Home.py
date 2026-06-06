# streamlit dashboard entry point (evolved from cashflow_2026_streamlit.py)
# run in terminal: streamlit run streamlit_app/Home.py

"""
what it is:
simulation of weekly cashflow that minimizes interest

features:
1. debt avalanche method: prioritizes extra cash towards the highest interest
   debts first (CC at 21.99% vs. LOC at 5.45%).
2. expense floating: uses the Credit Card grace period to float eligible living
   and housing costs interest-free.
3. LOC reborrowing: automates the Credit Card payoff on the due date using
   bank funds. If insufficient, it draws from the lower-interest LOC to
   prevent high-interest CC charges.
4. payment frequencies: handles multiple payment frequencies including
   weekly, bi-weekly, monthly,  bi-monthly, and quarterly.
5. dynamic date: gives balance on target date or date of debt pay-off (if sooner).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from streamlit_app.components.mortgage_profile import init_mortgage_profile
from streamlit_app.components.session_state import init_cashflow_config
from streamlit_app.components.styles import APP_CSS
from streamlit_app.pages import cashflow, mortgage_prepayment

st.set_page_config(page_title="Personal Finance", layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)

init_mortgage_profile()
init_cashflow_config()

pg = st.navigation([
    st.Page(cashflow.render, title="Cashflow and Debt", icon="💰", url_path="cashflow", default=True),
    st.Page(mortgage_prepayment.render, title="Mortgage Prepayment", icon="🏠", url_path="mortgage-prepayment"),
])
pg.run()
