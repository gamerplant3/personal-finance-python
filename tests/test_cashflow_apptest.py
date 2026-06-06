"""AppTest coverage for dashboard load and input persistence."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _sidebar_widget(app, label_substring: str):
    for widget in app.sidebar:
        label = getattr(widget, "label", None)
        if label and label_substring in str(label):
            return widget
    return None


def test_cashflow_page_loads():
    app = AppTest.from_file(ROOT / "streamlit_app" / "Home.py", default_timeout=30)
    app.run()
    assert not app.exception


def test_cashflow_bank_balance_persists_across_reruns():
    app = AppTest.from_file(ROOT / "streamlit_app" / "Home.py", default_timeout=30)
    app.run()

    bank = _sidebar_widget(app, "Starting Bank")
    assert bank is not None
    assert bank.value == 1500.0

    bank.set_value(8888.0)
    app.run()
    assert _sidebar_widget(app, "Starting Bank").value == 8888.0

    app.run()
    assert _sidebar_widget(app, "Starting Bank").value == 8888.0
    assert app.session_state["cashflow_config"].bank_balance == 8888.0


def test_mortgage_profile_reflected_on_cashflow_sidebar():
    """Mortgage session profile is shared when cashflow page shows read-only summary."""
    app = AppTest.from_file(ROOT / "streamlit_app" / "Home.py", default_timeout=30)
    app.run()

    app.session_state.mortgage["principal"] = 620000.0
    app.run()

    summary = next(
        (
            str(getattr(widget, "value", ""))
            for widget in app.sidebar
            if "620,000" in str(getattr(widget, "value", ""))
        ),
        "",
    )
    assert "620,000" in summary
    assert app.session_state["mortgage"]["principal"] == 620000.0
