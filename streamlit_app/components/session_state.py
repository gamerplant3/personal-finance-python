"""Shared session-state helpers for persisting inputs across page navigation."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from cashflow_engine import DEFAULT_LOC_LIMIT, CashflowConfig, tracked_debts
from streamlit_app.components.coerce import (
    debts_editor_df,
    expenses_editor_df,
    windfalls_editor_df,
)

CASHFLOW_CFG_KEY = "cashflow_config"
DEBTS_DF_KEY = "cf_debts_editor_df"
EXPENSES_DF_KEY = "cf_expenses_editor_df"
WINDFALLS_DF_KEY = "cf_windfalls_editor_df"
EDITOR_WIDGET_KEYS = ("debts_editor", "expenses_editor", "windfalls_editor")


def _ensure_widget_key(key: str, value: object) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def init_cashflow_config() -> None:
    if CASHFLOW_CFG_KEY in st.session_state:
        return
    cfg = CashflowConfig.default()
    profile = st.session_state.get("profile", {})
    if "bank_balance" in profile:
        cfg.bank_balance = float(profile["bank_balance"])
    if "loc_limit" in profile:
        cfg.loc_limit = float(profile["loc_limit"])
    st.session_state[CASHFLOW_CFG_KEY] = cfg


def get_cashflow_config() -> CashflowConfig:
    init_cashflow_config()
    cfg = st.session_state[CASHFLOW_CFG_KEY]
    filtered = tracked_debts(cfg.debts)
    if len(filtered) != len(cfg.debts):
        cfg.debts = filtered
        st.session_state[CASHFLOW_CFG_KEY] = cfg
    return cfg


def save_cashflow_config(cfg: CashflowConfig) -> None:
    st.session_state[CASHFLOW_CFG_KEY] = cfg
    profile = st.session_state.setdefault("profile", {})
    profile["bank_balance"] = cfg.bank_balance
    profile["loc_limit"] = cfg.loc_limit


def reset_cashflow_editor_tables(cfg: CashflowConfig) -> None:
    """Rebuild data-editor source tables after scenario load or external config change."""
    st.session_state[DEBTS_DF_KEY] = debts_editor_df(cfg.debts)
    st.session_state[EXPENSES_DF_KEY] = expenses_editor_df(cfg.expenses)
    st.session_state[WINDFALLS_DF_KEY] = windfalls_editor_df(cfg.windfalls)
    for key in EDITOR_WIDGET_KEYS:
        st.session_state.pop(key, None)


def seed_cashflow_sidebar_widgets(cfg: CashflowConfig) -> None:
    """Initialize widget session keys once; avoids value= fighting key= on reruns."""
    _ensure_widget_key("cf_bank_balance", float(cfg.bank_balance))
    _ensure_widget_key("cf_min_buffer", float(cfg.min_bank_buffer))
    _ensure_widget_key("cf_loc_limit", float(cfg.loc_limit or DEFAULT_LOC_LIMIT))
    _ensure_widget_key("cf_start_date", cfg.start_date.date())
    _ensure_widget_key("cf_end_date", cfg.end_date.date())
    _ensure_widget_key("cf_income", float(cfg.income_biweekly))
    _ensure_widget_key("cf_next_pay", cfg.next_pay_date.date())
    _ensure_widget_key("cf_strategy", cfg.strategy)
    _ensure_widget_key("cf_cc_grace", bool(cfg.cc_grace_period))
    _ensure_widget_key("cf_scenario_name", cfg.scenario_name)


def apply_cashflow_sidebar_widgets(cfg: CashflowConfig) -> CashflowConfig:
    """Copy sidebar widget session values into the cashflow config object."""
    cfg.bank_balance = float(st.session_state.cf_bank_balance)
    cfg.min_bank_buffer = float(st.session_state.cf_min_buffer)
    cfg.loc_limit = float(st.session_state.cf_loc_limit)
    cfg.start_date = datetime.combine(st.session_state.cf_start_date, datetime.min.time())
    cfg.end_date = datetime.combine(st.session_state.cf_end_date, datetime.min.time())
    cfg.income_biweekly = float(st.session_state.cf_income)
    cfg.next_pay_date = datetime.combine(st.session_state.cf_next_pay, datetime.min.time())
    cfg.strategy = st.session_state.cf_strategy
    cfg.cc_grace_period = bool(st.session_state.cf_cc_grace)
    cfg.scenario_name = str(st.session_state.cf_scenario_name)
    return cfg


def get_debts_editor_df(cfg: CashflowConfig):
    if DEBTS_DF_KEY not in st.session_state:
        st.session_state[DEBTS_DF_KEY] = debts_editor_df(cfg.debts)
    return st.session_state[DEBTS_DF_KEY]


def get_expenses_editor_df(cfg: CashflowConfig):
    if EXPENSES_DF_KEY not in st.session_state:
        st.session_state[EXPENSES_DF_KEY] = expenses_editor_df(cfg.expenses)
    return st.session_state[EXPENSES_DF_KEY]


def get_windfalls_editor_df(cfg: CashflowConfig):
    if WINDFALLS_DF_KEY not in st.session_state:
        st.session_state[WINDFALLS_DF_KEY] = windfalls_editor_df(cfg.windfalls)
    return st.session_state[WINDFALLS_DF_KEY]


def store_debts_editor_df(df) -> None:
    st.session_state[DEBTS_DF_KEY] = df


def store_expenses_editor_df(df) -> None:
    st.session_state[EXPENSES_DF_KEY] = df


def store_windfalls_editor_df(df) -> None:
    st.session_state[WINDFALLS_DF_KEY] = df
