"""Session-state helpers keep widget defaults from overwriting user edits."""

from datetime import datetime

from cashflow_engine import CashflowConfig, DebtConfig

from streamlit_app.components.session_state import (
    CASHFLOW_CFG_KEY,
    DEBTS_DF_KEY,
    apply_cashflow_sidebar_widgets,
    reset_cashflow_editor_tables,
    seed_cashflow_sidebar_widgets,
)


class _FakeSessionState(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


def test_seed_cashflow_widgets_only_runs_once():
    cfg = CashflowConfig(bank_balance=2000.0, min_bank_buffer=250.0)
    state = _FakeSessionState()
    state[CASHFLOW_CFG_KEY] = cfg

    import streamlit_app.components.session_state as ss

    original = ss.st.session_state
    ss.st.session_state = state
    try:
        seed_cashflow_sidebar_widgets(cfg)
        assert state["cf_bank_balance"] == 2000.0
        assert state["cf_min_buffer"] == 250.0

        state["cf_bank_balance"] = 9999.0
        seed_cashflow_sidebar_widgets(cfg)
        assert state["cf_bank_balance"] == 9999.0
    finally:
        ss.st.session_state = original


def test_apply_cashflow_sidebar_widgets_reads_widget_keys():
    cfg = CashflowConfig()
    state = _FakeSessionState(
        cf_bank_balance=4321.0,
        cf_min_buffer=100.0,
        cf_loc_limit=50000.0,
        cf_start_date=datetime(2026, 3, 1).date(),
        cf_end_date=datetime(2026, 12, 31).date(),
        cf_income=3000.0,
        cf_next_pay=datetime(2026, 3, 6).date(),
        cf_strategy="snowball",
        cf_cc_grace=False,
        cf_scenario_name="Test",
    )

    import streamlit_app.components.session_state as ss

    original = ss.st.session_state
    ss.st.session_state = state
    try:
        updated = apply_cashflow_sidebar_widgets(cfg)
        assert updated.bank_balance == 4321.0
        assert updated.strategy == "snowball"
        assert updated.cc_grace_period is False
        assert updated.scenario_name == "Test"
    finally:
        ss.st.session_state = original


def test_seed_mortgage_widgets_preserves_user_edits():
    from mortgage_math import DEFAULT_PRINCIPAL, default_mortgage_scenario
    from streamlit_app.components.mortgage_profile import _seed_mortgage_widgets

    m = default_mortgage_scenario()
    state = _FakeSessionState()

    import streamlit_app.components.mortgage_profile as mp

    original = mp.st.session_state
    mp.st.session_state = state
    try:
        _seed_mortgage_widgets(m)
        assert state["mp_principal"] == DEFAULT_PRINCIPAL
        state["mp_principal"] = 610000.0
        _seed_mortgage_widgets(m)
        assert state["mp_principal"] == 610000.0
    finally:
        mp.st.session_state = original


def test_reset_cashflow_editor_tables_rebuilds_from_config():
    cfg = CashflowConfig(
        debts=[DebtConfig("LOC", 12000.0, 0.05)],
    )
    state = _FakeSessionState({DEBTS_DF_KEY: "stale"})

    import streamlit_app.components.session_state as ss

    original = ss.st.session_state
    ss.st.session_state = state
    try:
        reset_cashflow_editor_tables(cfg)
        assert state[DEBTS_DF_KEY].iloc[0]["desc"] == "LOC"
        assert state[DEBTS_DF_KEY].iloc[0]["bal"] == 12000.0
        assert "debts_editor" not in state
    finally:
        ss.st.session_state = original
