"""Type coercion helpers for Streamlit widget and data_editor values."""

import math
import warnings
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any
import pandas as pd
import streamlit as st

PLACEHOLDER_DESC = "Empty"

def as_float(val, default: float = 0.0) -> float:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return default

    return float(val)

def as_date(val) -> date:
    if isinstance(val, datetime):
        return val.date()

    if isinstance(val, date):
        return val

    if hasattr(val, "date"):
        return val.date()

    return val

def as_datetime(val) -> datetime:
    return datetime.combine(as_date(val), datetime.min.time())

def is_placeholder_desc(desc: object) -> bool:
    if desc is None:
        return True

    text = str(desc).strip()
    return text == "" or text == PLACEHOLDER_DESC

_PANDAS_EDITOR_WARNINGS = (
    "The behavior of DataFrame concatenation with empty or all-NA entries is deprecated",
    "Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated",
)

@contextmanager

def _suppress_data_editor_warnings():
    with warnings.catch_warnings():
        for message in _PANDAS_EDITOR_WARNINGS:
            warnings.filterwarnings(
                "ignore",
                message=f".*{message}.*",
                category=FutureWarning,
            )

        yield

def safe_data_editor(data: pd.DataFrame, /, **kwargs: Any) -> pd.DataFrame:
    with _suppress_data_editor_warnings():
        return st.data_editor(data, **kwargs)

def _is_missing(val: object) -> bool:
    if val is None or val is pd.NA:
        return True

    if isinstance(val, float) and math.isnan(val):
        return True

    return False

def _coerce_str(val: object, default: str = PLACEHOLDER_DESC) -> str:
    if _is_missing(val):
        return default

    text = str(val).strip()
    return default if text == "" else text

def _coerce_float(val: object, default: float = 0.0) -> float:
    if _is_missing(val):
        return default

    return float(val)

def _coerce_bool(val: object, default: bool = False) -> bool:
    if _is_missing(val):
        return default

    return bool(val)

def _editor_df(rows: list[dict], columns: dict[str, str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame({name: pd.Series(dtype=dtype) for name, dtype in columns.items()})

    df = pd.DataFrame(rows)
    for name, dtype in columns.items():
        if name not in df.columns:
            df[name] = pd.Series(dtype=dtype)

        if dtype == "Int64":
            df[name] = pd.array(df[name], dtype="Int64")

        else:
            df[name] = df[name].astype(dtype)

    return df[list(columns)]

def _blank_debt_row() -> dict:
    return {
        "desc": PLACEHOLDER_DESC,
        "bal": 0.0,
        "rate": 0.0,
        "due_day": 0.0,
        "is_credit_card": False,
    }

def normalize_debts_df(df: pd.DataFrame) -> pd.DataFrame:
    blank = _blank_debt_row()
    if df.empty:
        return pd.DataFrame([blank], columns=list(blank.keys()))

    rows = []
    for record in df.to_dict("records"):
        rows.append({
            "desc": _coerce_str(record.get("desc"), blank["desc"]),
            "bal": _coerce_float(record.get("bal"), blank["bal"]),
            "rate": _coerce_float(record.get("rate"), blank["rate"]),
            "due_day": _coerce_float(record.get("due_day"), blank["due_day"]),
            "is_credit_card": _coerce_bool(record.get("is_credit_card"), blank["is_credit_card"]),
        })

    return pd.DataFrame(rows, columns=list(blank.keys()))

def debts_editor_df(debts) -> pd.DataFrame:
    rows = [d.to_dict() for d in debts]
    if not rows:
        return normalize_debts_df(pd.DataFrame([_blank_debt_row()]))

    df = _editor_df(
        rows,
        {
            "desc": "string",
            "bal": "float64",
            "rate": "float64",
            "due_day": "float64",
            "is_credit_card": "bool",
        },
    )
    return normalize_debts_df(df)

def _blank_expense_row() -> dict:
    return {
        "desc": PLACEHOLDER_DESC,
        "amt": 0.0,
        "freq": "weekly",
        "day": 0,
        "use_cc": False,
    }

def normalize_expenses_df(df: pd.DataFrame) -> pd.DataFrame:
    blank = _blank_expense_row()
    if df.empty:
        return pd.DataFrame([blank], columns=list(blank.keys()))

    rows = []
    for record in df.to_dict("records"):
        freq = record.get("freq")
        rows.append({
            "desc": _coerce_str(record.get("desc"), blank["desc"]),
            "amt": _coerce_float(record.get("amt"), blank["amt"]),
            "freq": blank["freq"] if _is_missing(freq) or str(freq).strip() == "" else str(freq),
            "day": int(_coerce_float(record.get("day"), blank["day"])),
            "use_cc": _coerce_bool(record.get("use_cc"), blank["use_cc"]),
        })

    return pd.DataFrame(rows, columns=list(blank.keys()))

def expenses_editor_df(expenses) -> pd.DataFrame:
    rows = [e.to_dict() for e in expenses]
    if not rows:
        return normalize_expenses_df(pd.DataFrame([_blank_expense_row()]))

    df = _editor_df(
        rows,
        {
            "desc": "string",
            "amt": "float64",
            "freq": "string",
            "day": "int64",
            "use_cc": "bool",
        },
    )
    return normalize_expenses_df(df)

def _blank_windfall_row() -> dict:
    return {
        "desc": PLACEHOLDER_DESC,
        "amt": 0.0,
        "date": date.today(),
    }

def normalize_windfalls_df(df: pd.DataFrame) -> pd.DataFrame:
    blank = _blank_windfall_row()
    if df.empty:
        return pd.DataFrame([blank], columns=list(blank.keys()))

    rows = []
    for record in df.to_dict("records"):
        row_date = record.get("date")
        rows.append({
            "desc": _coerce_str(record.get("desc"), blank["desc"]),
            "amt": _coerce_float(record.get("amt"), blank["amt"]),
            "date": blank["date"] if _is_missing(row_date) else as_date(row_date),
        })

    return pd.DataFrame(rows, columns=list(blank.keys()))

def windfalls_editor_df(windfalls) -> pd.DataFrame:
    rows = [{"desc": w.desc, "amt": w.amt, "date": w.date.date()} for w in windfalls]
    if not rows:
        return normalize_windfalls_df(pd.DataFrame([_blank_windfall_row()]))

    df = _editor_df(
        rows,
        {"desc": "string", "amt": "float64", "date": "object"},
    )
    return normalize_windfalls_df(df)
