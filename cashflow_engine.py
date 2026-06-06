"""
Unified weekly cashflow simulation engine.
Extracted from cashflow_2026_streamlit.py.
Powers the Streamlit dashboard and direct Python imports.
"""

from __future__ import annotations
import copy
import math
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Literal
import pandas as pd

FREQUENCIES = ["weekly", "bi-weekly", "monthly", "bi-monthly", "quarterly"]
DEBT_STRATEGIES = ["avalanche", "snowball", "cc_first"]
STRATEGIES = DEBT_STRATEGIES

DEFAULT_LOC_LIMIT = 50_000.0
DEFAULT_BANK_BALANCE = 1_500.0

def is_mortgage_debt(desc: str) -> bool:
    """True when a debt row represents mortgage principal (tracked as expense only)."""
    return "mortgage" in str(desc).strip().lower()

def tracked_debts(debts: list[DebtConfig]) -> list[DebtConfig]:
    """Debts included in payoff simulation, totals, and debt-free metrics."""
    return [d for d in debts if not is_mortgage_debt(d.desc)]

def next_friday_after(d: date) -> date:
    days_ahead = (4 - d.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return d + timedelta(days=days_ahead)

def _default_start_date() -> datetime:
    return datetime.combine(date.today(), datetime.min.time())

def _default_end_date() -> datetime:
    today = date.today()
    return datetime.combine(date(today.year, 12, 31), datetime.min.time())

def _default_next_pay_date() -> datetime:
    return datetime.combine(next_friday_after(date.today()), datetime.min.time())

@dataclass

class DebtConfig:
    desc: str
    bal: float
    rate: float
    due_day: int | None = None
    is_credit_card: bool = False
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> DebtConfig:
        dd = dict(d)
        due = dd.get("due_day")
        if due is None or (isinstance(due, float) and math.isnan(due)) or due == 0:
            dd["due_day"] = None
        else:
            dd["due_day"] = int(due)
        dd["bal"] = float(dd["bal"])
        dd["rate"] = float(dd["rate"])
        return cls(**dd)

@dataclass

class ExpenseConfig:
    desc: str
    amt: float
    freq: str
    day: int
    use_cc: bool = False
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> ExpenseConfig:
        dd = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        dd["amt"] = float(dd["amt"])
        dd["day"] = int(dd["day"])
        return cls(**dd)

@dataclass

class WindfallConfig:
    desc: str
    amt: float
    date: datetime
    def to_dict(self) -> dict:
        d = asdict(self)
        d["date"] = self.date.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> WindfallConfig:
        dd = dict(d)
        if isinstance(dd["date"], str):
            dd["date"] = datetime.fromisoformat(dd["date"])
        return cls(**dd)

@dataclass

class SimulationConfig:
    bank_balance: float = DEFAULT_BANK_BALANCE
    min_bank_buffer: float = 100.0
    emergency_fund_target: float = 0.0
    start_date: datetime = field(default_factory=_default_start_date)
    end_date: datetime = field(default_factory=_default_end_date)
    income_biweekly: float = 2500.0
    next_pay_date: datetime = field(default_factory=_default_next_pay_date)
    debts: list[DebtConfig] = field(default_factory=list)
    expenses: list[ExpenseConfig] = field(default_factory=list)
    windfalls: list[WindfallConfig] = field(default_factory=list)
    strategy: Literal["avalanche", "snowball", "cc_first"] = "avalanche"
    cc_grace_period: bool = True
    loc_limit: float | None = DEFAULT_LOC_LIMIT
    income_multiplier: float = 1.0
    expense_multiplier: float = 1.0
    scenario_name: str = "Baseline"
    def to_dict(self) -> dict:
        return {
            "bank_balance": self.bank_balance,
            "min_bank_buffer": self.min_bank_buffer,
            "emergency_fund_target": self.emergency_fund_target,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "income_biweekly": self.income_biweekly,
            "next_pay_date": self.next_pay_date.isoformat(),
            "debts": [d.to_dict() for d in self.debts],
            "expenses": [e.to_dict() for e in self.expenses],
            "windfalls": [w.to_dict() for w in self.windfalls],
            "strategy": self.strategy,
            "cc_grace_period": self.cc_grace_period,
            "loc_limit": self.loc_limit,
            "income_multiplier": self.income_multiplier,
            "expense_multiplier": self.expense_multiplier,
            "scenario_name": self.scenario_name,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SimulationConfig:
        dd = dict(d)
        for key in ("start_date", "end_date", "next_pay_date"):
            if isinstance(dd.get(key), str):
                dd[key] = datetime.fromisoformat(dd[key])
        dd["debts"] = tracked_debts(
            [DebtConfig.from_dict(x) for x in dd.get("debts", [])],
        )
        dd["expenses"] = [ExpenseConfig.from_dict(x) for x in dd.get("expenses", [])]
        dd["windfalls"] = [WindfallConfig.from_dict(x) for x in dd.get("windfalls", [])]
        return cls(**{k: v for k, v in dd.items() if k in cls.__dataclass_fields__})

    @classmethod
    def default(cls) -> SimulationConfig:
        return cls(
            debts=[
                DebtConfig("Credit Card 1", 4000.0, 0.2199, due_day=9, is_credit_card=True),
                DebtConfig("Credit Card 2", 2000.0, 0.2199, due_day=25, is_credit_card=True),
                DebtConfig("LOC", 1000.0, 0.0545),
            ],
            expenses=[
                ExpenseConfig("Living Expense", 250.0, "weekly", 0, use_cc=True),
                ExpenseConfig("Mortgage", 446.15, "weekly", 3, use_cc=False),
                ExpenseConfig("Condo Fees", 900.0, "monthly", 1),
                ExpenseConfig("Home Insurance", 80.0, "monthly", 1, use_cc=True),
                ExpenseConfig("Property Tax", 250.0, "monthly", 1),
            ],
            windfalls=[
                WindfallConfig("Gift", 1000.0, datetime(2026, 6, 15)),
            ],
        )

@dataclass

class SimulationResult:
    df: pd.DataFrame
    payment_table: list[dict]
    metrics: dict[str, Any]

CashflowConfig = SimulationConfig

def apply_sensitivity(config: SimulationConfig, **kwargs) -> SimulationConfig:
    c = copy.deepcopy(config)
    for k, v in kwargs.items():
        if hasattr(c, k):
            setattr(c, k, v)
    return c

def monthly_expense_total(expenses: list[ExpenseConfig]) -> float:
    total = 0.0
    for cost in expenses:
        amt = float(cost.amt)
        if cost.freq == "weekly":
            total += amt * 52 / 12
        elif cost.freq == "bi-weekly":
            total += amt * 26 / 12
        elif cost.freq == "monthly":
            total += amt
        elif cost.freq == "bi-monthly":
            total += amt / 2
        elif cost.freq == "quarterly":
            total += amt / 3
    return total

def emergency_fund_target_from_expenses(expenses: list[ExpenseConfig], months: int = 3) -> float:
    return monthly_expense_total(expenses) * months

def _expense_hits(cost: ExpenseConfig, d: datetime, start_date: datetime) -> bool:
    day = int(cost.day)
    if cost.freq == "weekly":
        return d.weekday() == day
    if cost.freq == "bi-weekly":
        return (d - start_date).days % 14 == 0
    if cost.freq == "monthly":
        return d.day == day
    if cost.freq == "bi-monthly":
        month_diff = (d.year - start_date.year) * 12 + (d.month - start_date.month)
        return month_diff % 2 == 0 and d.day == day
    if cost.freq == "quarterly":
        return d.day == day and d.month in (3, 6, 9, 12)
    return False

def _primary_cc(loans: list[dict]) -> dict | None:
    for l in loans:
        if l.get("is_credit_card"):
            return l
    return loans[0] if loans else None

def _primary_loc(loans: list[dict]) -> dict | None:
    for l in loans:
        if "loc" in l["desc"].lower() or l["desc"] == "LOC":
            return l
    return None

def _sort_debts_for_payment(loans: list[dict], strategy: str) -> list[dict]:
    payable = [l for l in loans if l["bal"] > 0.01]
    if strategy == "snowball":
        return sorted(payable, key=lambda x: x["bal"])
    if strategy == "cc_first":
        return sorted(payable, key=lambda x: (not x.get("is_credit_card", False), -x["rate"]))
    return sorted(payable, key=lambda x: -x["rate"])

def _loans_from_config(config: SimulationConfig) -> list[dict]:
    return [copy.deepcopy({
        "desc": d.desc, "bal": float(d.bal), "rate": float(d.rate),
        "due_day": int(d.due_day) if d.due_day is not None else None,
        "is_credit_card": d.is_credit_card,
    }) for d in tracked_debts(config.debts)]

def _scaled_expenses(config: SimulationConfig) -> list[ExpenseConfig]:
    mult = config.expense_multiplier
    out = []
    for e in config.expenses:
        ec = copy.deepcopy(e)
        ec.amt = round(ec.amt * mult, 2)
        out.append(ec)
    return out

def run_cashflow_simulation(config: SimulationConfig) -> SimulationResult:
    start_date = config.start_date
    end_date = config.end_date
    next_pay_date = config.next_pay_date
    income = config.income_biweekly * config.income_multiplier
    expenses = _scaled_expenses(config)
    loans = _loans_from_config(config)
    cc = _primary_cc(loans)
    loc = _primary_loc(loans)

    number_of_weeks = max(1, ((end_date - start_date).days // 7) + 1)
    sim_bank = float(config.bank_balance)
    total_interest = 0.0
    data = []
    payment_table = []
    peak_loc = loc["bal"] if loc else 0.0
    buffer_breaches = 0
    loc_limit_breaches = 0
    emergency_target = config.emergency_fund_target or config.min_bank_buffer
    current_date = start_date
    for week in range(number_of_weeks):
        week_start = current_date
        inflows, outflows = [], []
        payment_made = False
        weekly_income = 0.0
        weekly_expense = 0.0
        for i in range(7):
            d = week_start + timedelta(days=i)
            if d > end_date:
                break
            if (d - next_pay_date).days % 14 == 0 and d >= next_pay_date:
                weekly_income += income
            for w in config.windfalls:
                if d.date() == w.date.date():
                    weekly_income += w.amt * config.income_multiplier
            for cost in expenses:
                if _expense_hits(cost, d, start_date):
                    weekly_expense += cost.amt

        for i in range(7):
            d = week_start + timedelta(days=i)
            if d > end_date:
                break

            if (d - next_pay_date).days % 14 == 0 and d >= next_pay_date:
                sim_bank += income
                inflows.append(f"Pay: +${income:,.2f}")

            for w in config.windfalls:
                if d.date() == w.date.date():
                    windfall_amt = w.amt * config.income_multiplier
                    sim_bank += windfall_amt
                    inflows.append(f"{w.desc}: +${windfall_amt:,.2f}")

            for cost in expenses:
                if not _expense_hits(cost, d, start_date):
                    continue

                amt = cost.amt
                target_cc = cc if cost.use_cc and cc else None
                if target_cc:
                    target_cc["bal"] += amt
                    outflows.append(f"{cost.desc} (CC): -${amt:,.2f}")
                else:
                    if sim_bank - amt < config.min_bank_buffer and loc:
                        available = max(0, sim_bank - config.min_bank_buffer)
                        needed = amt - available
                        loc["bal"] += needed
                        sim_bank += needed
                        outflows.append(f"LOC Float: +${needed:,.2f}")
                        payment_table.append(_pt_row(week_start, weekly_income, weekly_expense,
                                                     "Line of Credit", loc["bal"],
                                                     f"{cost.desc} (LOC Cover)", "", needed))
                        payment_made = True
                    else:
                        payment_table.append(_pt_row(week_start, weekly_income, weekly_expense,
                                                     "Bank Account", sim_bank, cost.desc, "", amt))
                        payment_made = True
                    sim_bank -= amt
                    outflows.append(f"{cost.desc}: -${amt:,.2f}")

            for loan in loans:
                if not loan.get("is_credit_card") or not loan.get("due_day"):
                    continue
                if d.day != int(loan["due_day"]):
                    continue
                if loan["bal"] <= 0:
                    continue
                payment_needed = loan["bal"]
                bank_contrib = max(0.0, min(sim_bank - config.min_bank_buffer, payment_needed))
                if bank_contrib > 0:
                    payment_table.append(_pt_row(week_start, weekly_income, weekly_expense,
                                                   "Bank Account", sim_bank, loan["desc"],
                                                   loan["bal"], bank_contrib))
                    sim_bank -= bank_contrib
                    payment_made = True
                loc_contrib = payment_needed - bank_contrib
                if loc_contrib > 0 and loc:
                    loc["bal"] += loc_contrib
                    outflows.append(f"LOC Float (CC): +${loc_contrib:,.2f}")
                    payment_table.append(_pt_row(week_start, weekly_income, weekly_expense,
                                                   "Line of Credit", loc["bal"], loan["desc"],
                                                   loan["bal"] - bank_contrib, loc_contrib))
                    payment_made = True
                outflows.append(f"CC Payment: -${payment_needed:,.2f}")
                loan["bal"] = 0

        for loan in loans:
            accrues = not (loan.get("is_credit_card") and config.cc_grace_period)
            if accrues and loan["bal"] > 0:
                weekly_int = round((loan["bal"] * loan["rate"]) / 52, 2)
                loan["bal"] += weekly_int
                total_interest += weekly_int

        for loan in _sort_debts_for_payment(loans, config.strategy):
            if sim_bank <= config.min_bank_buffer or loan["bal"] <= 0:
                continue
            payment = min(sim_bank - config.min_bank_buffer, loan["bal"])
            if payment > 0.01:
                payment_table.append(_pt_row(week_start, weekly_income, weekly_expense,
                                               "Bank Account", sim_bank, loan["desc"],
                                               loan["bal"], payment))
                loan["bal"] -= round(payment, 2)
                sim_bank -= round(payment, 2)
                outflows.append(f"Paid {loan['desc']}: -${payment:,.2f}")
                payment_made = True

        if not payment_made:
            payment_table.append(_pt_row(week_start, weekly_income, weekly_expense,
                                         "Bank Account", sim_bank, "", "", 0))

        if loc:
            peak_loc = max(peak_loc, loc["bal"])
            if config.loc_limit and loc["bal"] > config.loc_limit:
                loc_limit_breaches += 1
        if sim_bank < emergency_target:
            buffer_breaches += 1

        row = {
            "Date": week_start,
            "Total Debt": round(sum(l["bal"] for l in loans), 2),
            "Bank": round(sim_bank, 2),
            "Cumulative Interest": round(total_interest, 2),
            "Details": "<b>Weekly Detail:</b><br>" + "<br>".join(inflows + outflows),
        }
        for loan in loans:
            row[loan["desc"]] = round(loan["bal"], 2)
        data.append(row)
        current_date += timedelta(days=7)

    df = pd.DataFrame(data)
    zero_row = df[df["Total Debt"] <= 0.01].head(1)
    debt_free = zero_row["Date"].iloc[0].strftime("%Y-%m-%d") if not zero_row.empty else None
    metrics = {
        "debt_free_date": debt_free,
        "total_interest": round(total_interest, 2),
        "final_bank_balance": round(sim_bank, 2),
        "peak_loc_balance": round(peak_loc, 2),
        "buffer_breaches": buffer_breaches,
        "loc_limit_breaches": loc_limit_breaches,
        "end_total_debt": round(df["Total Debt"].iloc[-1], 2) if len(df) else 0,
        "emergency_fund_target": emergency_target,
        "weeks_to_emergency_fund": _weeks_to_emergency_fund(
            df, float(config.bank_balance), emergency_target,
        ),
        "scenario_name": config.scenario_name,
    }

    return SimulationResult(df=df, payment_table=payment_table, metrics=metrics)

def _weeks_to_emergency_fund(df: pd.DataFrame, start_balance: float, target: float) -> int | None:
    if target <= 0:
        return None
    if start_balance >= target:
        return 0
    reached = df[df["Bank"] >= target]
    if reached.empty:
        return None
    return int(reached.index[0]) + 1

def _pt_row(week_start, income, expenses, source, source_bal, dest, dest_bal, amount) -> dict:
    return {
        "Week": week_start.strftime("%Y-%m-%d"),
        "Income": f"${income:,.2f}",
        "Expenses": f"${expenses:,.2f}",
        "Source Account": source,
        "Source Balance": f"${source_bal:,.2f}" if isinstance(source_bal, (int, float)) else source_bal,
        "Destination": dest,
        "Dest. Balance": f"${dest_bal:,.2f}" if isinstance(dest_bal, (int, float)) and dest_bal != "" else dest_bal,
        "Amount to Pay": f"${amount:,.2f}",
    }

def compare_scenarios(configs: list[SimulationConfig]) -> pd.DataFrame:
    rows = []
    for index, cfg in enumerate(configs):
        result = run_cashflow_simulation(cfg)
        m = result.metrics
        rows.append({
            "Scenario": cfg.scenario_name or f"Scenario {index + 1}",
            "Debt Free Date": m.get("debt_free_date") or "Not in range",
            "Total Interest": f"${m['total_interest']:,.2f}",
            "Final Balance": f"${m['final_bank_balance']:,.2f}",
            "Peak LOC": f"${m['peak_loc_balance']:,.2f}",
            "Weeks to Full EF": (
                m["weeks_to_emergency_fund"]
                if m.get("weeks_to_emergency_fund") is not None
                else "Not in range"
            ),
            "End Debt": f"${m['end_total_debt']:,.2f}",
        })
    return pd.DataFrame(rows)

def payment_table_to_df(payment_table: list[dict]) -> pd.DataFrame:
    pay_df = pd.DataFrame(payment_table)
    if pay_df.empty:
        return pay_df
    mask = pay_df["Week"].duplicated()
    pay_df.loc[mask, ["Week", "Income", "Expenses"]] = ""
    return pay_df
