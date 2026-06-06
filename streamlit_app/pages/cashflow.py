"""Cashflow forecaster page with scenario comparison and sensitivity."""

import copy
import json
from datetime import datetime
import pandas as pd
import streamlit as st
from cashflow_engine import (
    FREQUENCIES,
    STRATEGIES,
    CashflowConfig,
    DebtConfig,
    ExpenseConfig,
    WindfallConfig,
    apply_sensitivity,
    compare_scenarios,
    emergency_fund_target_from_expenses,
    monthly_expense_total,
    payment_table_to_df,
    run_cashflow_simulation,
    tracked_debts,
)
from streamlit_app.components.charts import cashflow_chart
from streamlit_app.components.coerce import (
    as_datetime,
    as_float,
    is_placeholder_desc,
    normalize_debts_df,
    normalize_expenses_df,
    normalize_windfalls_df,
    safe_data_editor,
)
from streamlit_app.components.mortgage_profile import show_mortgage_sidebar_summary
from streamlit_app.components.session_state import (
    apply_cashflow_sidebar_widgets,
    get_cashflow_config,
    get_debts_editor_df,
    get_expenses_editor_df,
    get_windfalls_editor_df,
    reset_cashflow_editor_tables,
    save_cashflow_config,
    seed_cashflow_sidebar_widgets,
    store_debts_editor_df,
    store_expenses_editor_df,
    store_windfalls_editor_df,
)
from streamlit_app.components.styles import CASHFLOW_SIM_SUMMARY_CSS

def _config_from_sidebar() -> CashflowConfig:
    cfg = get_cashflow_config()
    seed_cashflow_sidebar_widgets(cfg)
    download_requested = False
    with st.sidebar:
        st.subheader("Profile")
        st.number_input("Starting Bank ($)", step=100.0, key="cf_bank_balance")
        st.number_input("Min Bank Buffer ($)", step=50.0, key="cf_min_buffer")
        st.number_input("LOC Limit ($)", step=1000.0, key="cf_loc_limit")
        st.divider()
        st.subheader("Timeline")
        c1, c2 = st.columns(2)
        c1.date_input("Start", key="cf_start_date")
        c2.date_input("End", key="cf_end_date")
        st.subheader("Income")
        c3, c4 = st.columns(2)
        c3.number_input("Bi-weekly Net ($)", step=100.0, key="cf_income")
        c4.date_input("Next Pay", key="cf_next_pay")
        st.subheader("Strategy")
        st.selectbox("Debt Payoff Strategy", STRATEGIES, key="cf_strategy")
        st.checkbox("CC Grace Period (no CC interest)", key="cf_cc_grace")
        show_mortgage_sidebar_summary()
        st.divider()
        st.subheader("Save / Load")
        st.text_input("Scenario Name", key="cf_scenario_name")
        up = st.file_uploader("Load JSON scenario", type=["json"], key="cf_scenario_upload")
        if up is not None:
            upload_id = f"{up.name}:{up.size}"
            if st.session_state.get("_last_scenario_upload_id") != upload_id:
                st.session_state["_last_scenario_upload_id"] = upload_id
                cfg = CashflowConfig.from_dict(json.loads(up.getvalue().decode()))
                save_cashflow_config(cfg)
                seed_cashflow_sidebar_widgets(cfg)
                reset_cashflow_editor_tables(cfg)
        if st.button("Download Scenario JSON", key="cf_download_btn"):
            download_requested = True

    cfg = apply_cashflow_sidebar_widgets(cfg)
    if download_requested:
        st.session_state["_download_scenario"] = cfg.to_dict()
    save_cashflow_config(cfg)
    return cfg

def _debts_expenses_windfalls_editor(cfg: CashflowConfig) -> CashflowConfig:
    st.subheader("Debts")
    edited_debts = safe_data_editor(
        get_debts_editor_df(cfg),
        num_rows="dynamic",
        column_config={
            "desc": "Description",
            "bal": st.column_config.NumberColumn("Balance", format="$%.2f"),
            "rate": st.column_config.NumberColumn("APR (decimal)", format="%.4f"),
            "due_day": st.column_config.NumberColumn("Due Day (CC)", min_value=1, max_value=28),
            "is_credit_card": st.column_config.CheckboxColumn("Credit Card?"),
        },
        hide_index=True,
        key="debts_editor",
    )
    edited_debts = normalize_debts_df(edited_debts)
    store_debts_editor_df(edited_debts)
    cfg.debts = tracked_debts([
        DebtConfig.from_dict(r) for r in edited_debts.to_dict("records")
        if not is_placeholder_desc(r.get("desc"))
    ])
    st.subheader("Expenses")
    edited_exp = safe_data_editor(
        get_expenses_editor_df(cfg),
        num_rows="dynamic",
        column_config={
            "desc": "Description",
            "amt": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "freq": st.column_config.SelectboxColumn("Frequency", options=FREQUENCIES),
            "day": st.column_config.NumberColumn("Day (0=Mon, 1-28)", min_value=0, max_value=28),
            "use_cc": st.column_config.CheckboxColumn("Pay via CC?"),
        },
        hide_index=True,
        key="expenses_editor",
    )
    edited_exp = normalize_expenses_df(edited_exp)
    store_expenses_editor_df(edited_exp)
    cfg.expenses = [
        ExpenseConfig.from_dict(r) for r in edited_exp.to_dict("records")
        if not is_placeholder_desc(r.get("desc"))
    ]
    st.subheader("Windfalls")
    edited_wind = safe_data_editor(
        get_windfalls_editor_df(cfg),
        num_rows="dynamic",
        hide_index=True,
        key="windfalls_editor",
        column_config={"date": st.column_config.DateColumn("Date")},
    )
    edited_wind = normalize_windfalls_df(edited_wind)
    store_windfalls_editor_df(edited_wind)
    cfg.windfalls = []
    for r in edited_wind.to_dict("records"):
        if not is_placeholder_desc(r.get("desc")):
            cfg.windfalls.append(WindfallConfig(
                r["desc"], as_float(r["amt"]),
                as_datetime(r["date"]),
            ))
    return cfg

def render():
    st.title("Cashflow and Debt Forecaster")
    cfg = _config_from_sidebar()
    tab_main, tab_compare, tab_sensitivity = st.tabs(["Simulation", "Scenario Compare", "Sensitivity"])
    with tab_main:
        cfg = _debts_expenses_windfalls_editor(cfg)
        cfg.emergency_fund_target = emergency_fund_target_from_expenses(cfg.expenses)
        monthly_expenses = monthly_expense_total(cfg.expenses)
        if st.session_state.get("_download_scenario"):
            st.download_button(
                "Save Scenario",
                data=json.dumps(st.session_state["_download_scenario"], indent=2),
                file_name=f"{cfg.scenario_name.replace(' ', '_')}.json",
                mime="application/json",
            )

        result = run_cashflow_simulation(cfg)
        m = result.metrics
        st.markdown(CASHFLOW_SIM_SUMMARY_CSS, unsafe_allow_html=True)
        r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
        r1c1.metric("Debt Free", m.get("debt_free_date") or "N/A")
        r1c2.metric("Total Interest", f"${m['total_interest']:,.2f}")
        r1c3.metric("Final Balance", f"${m['final_bank_balance']:,.2f}")
        r1c4.metric("Peak LOC", f"${m['peak_loc_balance']:,.2f}")
        r1c5.metric(
            "Emergency Fund",
            f"${cfg.emergency_fund_target:,.2f}",
            help=f"3× monthly expenses (${monthly_expenses:,.2f}/mo from expense table)",
        )
        if cfg.loc_limit and m["peak_loc_balance"] > cfg.loc_limit:
            st.error(f"LOC limit exceeded: peak ${m['peak_loc_balance']:,.2f} > limit ${cfg.loc_limit:,.2f} "
                     f"({m['loc_limit_breaches']} weeks over)")
        if m["buffer_breaches"] > 0:
            st.warning(f"Bank below emergency target for {m['buffer_breaches']} weeks")

        st.plotly_chart(
            cashflow_chart(result.df, m, cfg.emergency_fund_target),
            width="stretch",
            key="cashflow_main",
        )
        st.subheader("Weekly Cash Flow")
        pay_df = payment_table_to_df(result.payment_table)
        if not pay_df.empty:
            st.dataframe(pay_df, width="stretch", hide_index=True)
            csv_buf = pay_df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv_buf, "weekly_cashflow.csv", "text/csv")
        else:
            st.info("No payments in this period.")

    cfg.emergency_fund_target = emergency_fund_target_from_expenses(cfg.expenses)
    with tab_compare:
        st.markdown("Compare baseline against variations.")
        base = copy.deepcopy(cfg)
        base.scenario_name = "Baseline"
        scenarios = [base]
        if st.checkbox("Compare: No CC float (pay from bank)", value=True):
            no_cc = copy.deepcopy(cfg)
            no_cc.scenario_name = "No CC Float"
            for e in no_cc.expenses:
                e.use_cc = False
            scenarios.append(no_cc)

        if st.checkbox("Compare: Higher buffer ($1000)", value=True):
            hi_buf = copy.deepcopy(cfg)
            hi_buf.scenario_name = "Buffer $1000"
            hi_buf.min_bank_buffer = 1000.0
            scenarios.append(hi_buf)

        if st.checkbox("Compare: No windfalls"):
            no_wind = copy.deepcopy(cfg)
            no_wind.scenario_name = "No Windfalls"
            no_wind.windfalls = []
            scenarios.append(no_wind)

        if st.checkbox("Compare: Snowball strategy"):
            snow = copy.deepcopy(cfg)
            snow.scenario_name = "Snowball"
            snow.strategy = "snowball"
            scenarios.append(snow)

        st.dataframe(compare_scenarios(scenarios), width="stretch", hide_index=True)

    with tab_sensitivity:
        st.markdown("Adjust multipliers to see impact on debt-free date and interest.")
        s1, s2 = st.columns(2)
        income_mult = s1.slider("Income multiplier", 0.5, 1.5, 1.0, 0.05)
        expense_mult = s2.slider("Expense multiplier", 0.5, 1.5, 1.0, 0.05)
        sens_cfg = apply_sensitivity(cfg, income_multiplier=income_mult, expense_multiplier=expense_mult)
        sens_result = run_cashflow_simulation(sens_cfg)
        sm = sens_result.metrics
        s1c1, s1c2 = st.columns(2)
        s1c1.metric("Debt Free", sm.get("debt_free_date") or "N/A")
        s1c2.metric("Total Interest", f"${sm['total_interest']:,.2f}")
        s2c1, s2c2 = st.columns(2)
        s2c1.metric("Final Balance", f"${sm['final_bank_balance']:,.2f}")
        s2c2.metric("End Debt", f"${sm['end_total_debt']:,.2f}")
        st.plotly_chart(
            cashflow_chart(sens_result.df, sm, cfg.emergency_fund_target),
            width="stretch",
            key="cashflow_sensitivity",
        )

    save_cashflow_config(cfg)
