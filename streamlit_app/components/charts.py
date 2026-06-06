"""Plotly chart builders for finance dashboards."""

import plotly.graph_objects as go
import pandas as pd

def cashflow_chart(
    df: pd.DataFrame,
    metrics: dict,
    emergency_fund_target: float | None = None,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Total Debt"], name="Total Debt",
        hovertext=df.get("Details", ""), line=dict(color="#FF4B4B", width=2),
    ))
    for col, color, dash in [
        ("Bank", "#00D1FF", "dot"),
    ]:
        if col in df.columns and df[col].sum() > 0:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df[col], name=col,
                line=dict(color=color, width=2, dash=dash),
            ))
    debt_cols = [c for c in df.columns if c.endswith(" Balance")]
    palette = ["#FFA500", "#9370DB", "#FF69B4", "#20B2AA"]
    for i, col in enumerate(debt_cols):
        fig.add_trace(go.Scatter(
            x=df["Date"], y=df[col], name=col.replace(" Balance", ""),
            line=dict(color=palette[i % len(palette)], width=1, dash="dash"),
        ))
    if emergency_fund_target and emergency_fund_target > 0:
        fig.add_hline(
            y=emergency_fund_target,
            line_dash="dash",
            line_color="#32CD32",
            annotation_text=f"EF Target ${emergency_fund_target:,.2f}",
        )
    debt_free = metrics.get("debt_free_date")
    title_suffix = f"Debt Free: {debt_free}" if debt_free else f"End Debt: ${df['Total Debt'].iloc[-1]:,.2f}"
    fig.update_layout(
        title=f"Projection | {title_suffix} | Interest: ${metrics.get('total_interest', 0):,.2f}",
        hovermode="x unified", template="plotly_dark",
        yaxis=dict(title="Balance ($)", tickformat="$,.2f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig

# Midpoint between vibrant (#7209B7, #FF6B00) and muted (#9B7BB8, #C98B5A) series colors.
PREPAY_MONTHLY_COLOR = "#8642B8"
PREPAY_ACCELERATED_COLOR = "#E47B2D"
PREPAY_BAR_WIDTH = 0.15
_PREPAY_BAR_LAYOUT = dict(barmode="group", bargap=0.35, bargroupgap=0.1)
_PREPAY_ALIGNMENT_GROUP = "prepay"

def _extra_labels(extras: list) -> list[str]:
    return [f"${e:,.0f}" for e in extras]

def _prepayment_bar(
    name: str,
    x: list,
    y: list,
    color: str,
    offsetgroup: str,
) -> go.Bar:
    return go.Bar(
        name=name,
        x=x,
        y=y,
        marker_color=color,
        offsetgroup=offsetgroup,
        alignmentgroup=_PREPAY_ALIGNMENT_GROUP,
    )

def _apply_prepayment_bar_styling(fig: go.Figure) -> go.Figure:
    """Apply grouped-bar width and spacing shared by prepayment comparison charts."""
    fig.update_layout(**_PREPAY_BAR_LAYOUT)
    fig.update_traces(selector=dict(type="bar"), width=PREPAY_BAR_WIDTH)
    return fig

def prepayment_balance_comparison(
    extras: list,
    monthly_balances: list,
    acc_balances: list,
) -> go.Figure:
    labels = _extra_labels(extras)
    fig = go.Figure()
    fig.add_trace(_prepayment_bar(
        "Monthly", labels, monthly_balances, PREPAY_MONTHLY_COLOR, "monthly",
    ))
    fig.add_trace(_prepayment_bar(
        "Accelerated Weekly", labels, acc_balances, PREPAY_ACCELERATED_COLOR, "accelerated",
    ))
    fig.update_layout(
        title="Balance at Renewal - Monthly vs Accelerated Weekly",
        template="plotly_dark",
        xaxis=dict(title="Weekly prepayment amount ($)"),
        yaxis=dict(title="Balance ($)", tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return _apply_prepayment_bar_styling(fig)

def prepayment_interest_saved_comparison(
    extras: list,
    monthly_saved: list,
    acc_total_saved: list,
) -> go.Figure:
    labels = _extra_labels(extras)
    fig = go.Figure()
    fig.add_trace(_prepayment_bar(
        "Monthly Payments", labels, monthly_saved, PREPAY_MONTHLY_COLOR, "monthly",
    ))
    fig.add_trace(_prepayment_bar(
        "Accelerated Weekly", labels, acc_total_saved, PREPAY_ACCELERATED_COLOR, "accelerated",
    ))
    fig.update_layout(
        title="Interest Saved vs Monthly Baseline",
        template="plotly_dark",
        xaxis=dict(title="Weekly prepayment amount ($)"),
        yaxis=dict(title="Interest Saved ($)", tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return _apply_prepayment_bar_styling(fig)
