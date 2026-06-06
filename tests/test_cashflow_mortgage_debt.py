"""Mortgage principal must not appear in cashflow debt totals."""

from datetime import datetime

from cashflow_engine import (
    CashflowConfig,
    DebtConfig,
    ExpenseConfig,
    compare_scenarios,
    is_mortgage_debt,
    run_cashflow_simulation,
    tracked_debts,
)


def _short_config(*, with_mortgage_debt: bool) -> CashflowConfig:
    cfg = CashflowConfig(
        bank_balance=5000.0,
        min_bank_buffer=100.0,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 6, 30),
        income_biweekly=3000.0,
        next_pay_date=datetime(2026, 1, 3),
        debts=[
            DebtConfig("Credit Card", 4000.0, 0.2199, due_day=9, is_credit_card=True),
            DebtConfig("LOC", 15000.0, 0.0545),
        ],
        expenses=[
            ExpenseConfig("Mortgage", 1000.0, "weekly", 3, use_cc=False),
        ],
        windfalls=[],
        loc_limit=50_000.0,
    )
    if with_mortgage_debt:
        cfg.debts.append(DebtConfig("Mortgage", 750_000.0, 0.05))
    return cfg


def test_is_mortgage_debt_matches_common_labels():
    assert is_mortgage_debt("Mortgage")
    assert is_mortgage_debt("  mortgage principal  ")
    assert is_mortgage_debt("Home Mortgage")
    assert not is_mortgage_debt("LOC")
    assert not is_mortgage_debt("Credit Card")


def test_tracked_debts_strips_mortgage_rows():
    debts = [
        DebtConfig("LOC", 1000.0, 0.05),
        DebtConfig("Mortgage", 750_000.0, 0.05),
    ]
    assert len(tracked_debts(debts)) == 1
    assert tracked_debts(debts)[0].desc == "LOC"


def test_total_debt_excludes_mortgage_principal():
    with_mortgage = _short_config(with_mortgage_debt=True)
    without_mortgage = _short_config(with_mortgage_debt=False)

    result_with = run_cashflow_simulation(with_mortgage)
    result_without = run_cashflow_simulation(without_mortgage)

    assert "Mortgage" not in result_with.df.columns
    assert result_with.metrics["end_total_debt"] == result_without.metrics["end_total_debt"]
    assert result_with.df["Total Debt"].max() < 100_000.0


def test_final_bank_balance_matches_last_week():
    cfg = _short_config(with_mortgage_debt=False)
    result = run_cashflow_simulation(cfg)
    assert result.metrics["final_bank_balance"] == result.df["Bank"].iloc[-1]


def test_compare_scenarios_includes_final_balance():
    cfg = _short_config(with_mortgage_debt=False)
    table = compare_scenarios([cfg])
    assert "Final Balance" in table.columns
    assert "Lowest Bank" not in table.columns


def test_compare_scenarios_end_debt_excludes_mortgage():
    cfg = _short_config(with_mortgage_debt=True)
    table = compare_scenarios([cfg])
    end_debt = table.iloc[0]["End Debt"]
    assert end_debt != "$750,000.00"
    assert float(end_debt.replace("$", "").replace(",", "")) < 100_000.0


def test_from_dict_strips_mortgage_debt():
    raw = _short_config(with_mortgage_debt=True).to_dict()
    loaded = CashflowConfig.from_dict(raw)
    assert all(not is_mortgage_debt(d.desc) for d in loaded.debts)
