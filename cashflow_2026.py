# Cashflow forecaster that simulates weekly I/O. High interest debts are paid first, and when bank balance hits zero
# it re-borrows from LOC. Supports variable income and housing costs, and identifies date when debts are paid off.

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- INPUTS ---
income_biweekly = 2500
next_pay_date = datetime(2026, 2, 13)
bank_balance = 0
start_date = datetime(2026, 2, 3)
number_of_weeks = 52

loans = [
    {"desc": "Credit Card", "bal": 4000.0, "rate": 0.2199, "due": datetime(2026, 2, 9)},
    {"desc": "LOC", "bal": 14700.0, "rate": 0.0845}
]

housing_costs = [
    {"desc": "Mortgage", "amt": 495, "freq": "weekly", "day": 3},
    {"desc": "Condo Fees", "amt": 960, "freq": "monthly", "day": 1},
    {"desc": "Home Insurance", "amt": 80, "freq": "monthly", "day": 1},
    {"desc": "Property Tax", "amt": 600, "freq": "quarterly", "months": [3, 6, 9, 12], "day": 1}
]

windfalls = [{"desc": "April Bonus", "amt": 5000, "date": datetime(2026, 4, 15)}]
weekly_living = 1000 / 4

# --- SIMULATION ---
data = []
current_date = start_date # Restored iterator

for week in range(number_of_weeks):
    week_start = current_date
    week_end = current_date + timedelta(days=6)
    inflows = []
    outflows = []

    # 1. Income & Windfalls
    for i in range(7):
        d = week_start + timedelta(days=i)
        if (d - next_pay_date).days % 14 == 0 and d >= next_pay_date:
            bank_balance += income_biweekly
            inflows.append(f"Pay: +${income_biweekly:,.2f}")

    for w in windfalls:
        if week_start <= w['date'] <= week_end:
            bank_balance += w['amt']
            inflows.append(f"{w['desc']}: +${w['amt']:,.2f}")

    # 2. CC Payment (Feb 9)
    for l in loans:
        if l['desc'] == "Credit Card" and week_start <= l['due'] <= week_end and l['bal'] > 0:
            payment_amt = l['bal']
            bank_balance -= payment_amt
            outflows.append(f"CC Payment: -${payment_amt:,.2f}")
            l['bal'] = 0

    # 3. Housing & Living
    bank_balance -= weekly_living
    outflows.append(f"Living: -${weekly_living:,.2f}")
    for cost in housing_costs:
        for i in range(7):
            d = week_start + timedelta(days=i)
            if (cost['freq'] == "weekly" and d.weekday() == cost['day']) or \
               (cost['freq'] == "monthly" and d.day == cost['day']) or \
               (cost['freq'] == "quarterly" and d.day == cost['day'] and d.month in cost['months']):
                bank_balance -= cost['amt']
                outflows.append(f"{cost['desc']}: -${cost['amt']:,.2f}")

    # 4. Overdraft Prevention
    if bank_balance < 0:
        overdraft = abs(bank_balance)
        for l in loans:
            if l['desc'] == "LOC":
                l['bal'] += overdraft
                inflows.append(f"Borrowed: +${overdraft:,.2f}")
                bank_balance = 0

    # 5. Interest & Repayment
    for l in sorted(loans, key=lambda x: x['rate'], reverse=True):
        l['bal'] += (l['bal'] * l['rate']) / 52
        if bank_balance > 100 and l['bal'] > 0:
            payment = min(bank_balance - 100, l['bal'])
            l['bal'] -= payment
            bank_balance -= payment
            outflows.append(f"Repay {l['desc']}: -${payment:,.2f}")

    data.append({
        "Date": week_start,
        "LOC": round(loans[1]['bal'], 2),
        "CC": round(loans[0]['bal'], 2),
        "Details": "<b>Weekly Detail:</b><br>" + "<br>".join(inflows + outflows)
    })
    current_date += timedelta(days=7)

# --- FIND ZERO DATE ---
df = pd.DataFrame(data)
zero_row = df[df['LOC'] <= 0].head(1)
if not zero_row.empty:
    zero_date_str = zero_row['Date'].iloc[0].strftime("%b %d, %Y")
    annotation_text = f"Debt Free Date: {zero_date_str}"
else:
    remaining = df['LOC'].iloc[-1]
    annotation_text = f"End Balance: ${remaining:,.2f}"

# --- PLOT ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['LOC'], name='LOC Balance', hovertext=df['Details'], line=dict(color='firebrick', width=3)))

# Floating Annotation for "Time to 0"
fig.add_annotation(
    x=df['Date'].iloc[len(df)//2], y=df['LOC'].max() * 0.9,
    text=f"<b>{annotation_text}</b>",
    showarrow=False, font=dict(size=16, color="darkgreen"),
    bgcolor="white", bordercolor="darkgreen", borderwidth=2, borderpad=4
)

fig.update_layout(
    title="LOC Debt Paydown Timeline",
    hovermode="x unified",
    template="plotly_white",
    yaxis=dict(
        title="Balance ($)",
        tickformat="$,.2f",
        showgrid=True,
        gridcolor='LightGrey',
        zeroline=True,
        zerolinecolor='LightGrey',
        range=[0, df['LOC'].max() * 1.1]
    ),
    xaxis=dict(
        title="Timeline",
        showgrid=True,
        gridcolor='LightGrey'
    )
)
fig.show()