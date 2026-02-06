# cashflow forecaster that simulates weekly I/O to pay off debt
# run in IDE for localhost site

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

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- INPUTS ---
income_biweekly = 2500
next_pay_date = datetime(2026, 2, 13)
bank_balance = 0
min_bank_buffer = 100
start_date = datetime(2026, 2, 3)
end_date = datetime(2026, 12, 31)
number_of_weeks = max(1, ((end_date - start_date).days // 7) + 1)

loans = [
    {"desc": "Credit Card", "bal": 4000.0, "rate": 0.2199, "due_day": 9},
    {"desc": "LOC", "bal": 15000.0, "rate": 0.0545}
]

housing_costs = [
    {"desc": "Mortgage", "amt": 495, "freq": "weekly", "day": 3, "use_cc": False},
    {"desc": "Condo Fees", "amt": 960, "freq": "monthly", "day": 1, "use_cc": False},
    {"desc": "Home Insurance", "amt": 80, "freq": "monthly", "day": 1, "use_cc": True},
    {"desc": "Property Tax", "amt": 450, "freq": "bi-monthly", "day": 1, "use_cc": False}
]

windfalls = [{"desc": "April Bonus", "amt": 5000, "date": datetime(2026, 4, 15)}]
weekly_living = 250
living_use_cc = True

# --- SIMULATION ---
data = []
current_date = start_date
total_interest_paid = 0.0

for week in range(number_of_weeks):
    week_start = current_date
    week_end = current_date + timedelta(days=6)
    inflows = []
    outflows = []

    for i in range(7):
        d = week_start + timedelta(days=i)
        if d > end_date: break

        # Income & Windfalls
        if (d - next_pay_date).days % 14 == 0 and d >= next_pay_date:
            bank_balance += income_biweekly
            inflows.append(f"Pay: +${income_biweekly:,.2f}")

        for w in windfalls:
            if d.date() == w['date'].date():
                bank_balance += w['amt']
                inflows.append(f"{w['desc']}: +${w['amt']:,.2f}")

        # 2. CC Payment Logic
        if d.day == loans[0]['due_day']:
            if loans[0]['bal'] > 0:
                payment_needed = loans[0]['bal']
                # Bank pays what it can
                bank_contribution = max(0.0, min(bank_balance, payment_needed))
                bank_balance -= bank_contribution
                # LOC covers the rest
                loc_contribution = payment_needed - bank_contribution
                if loc_contribution > 0:
                    loans[1]['bal'] += loc_contribution
                    inflows.append(f"LOC cover CC: +${loc_contribution:,.2f}")

                outflows.append(f"CC Payment: -${payment_needed:,.2f}")
                loans[0]['bal'] = 0

        # 3. Housing & Living
        if d.weekday() == start_date.weekday():
            if living_use_cc:
                loans[0]['bal'] += weekly_living
                outflows.append(f"Living (CC): -${weekly_living:,.2f}")
            else:
                bank_balance -= weekly_living
                outflows.append(f"Living: -${weekly_living:,.2f}")

        # Housing Costs
        for cost in housing_costs:
            hit = False
            if cost['freq'] == "weekly" and d.weekday() == cost['day']:
                hit = True
            elif cost['freq'] == "bi-weekly" and (d - start_date).days % 14 == 0:
                hit = True
            elif cost['freq'] == "monthly" and d.day == cost['day']:
                hit = True
            elif cost['freq'] == "bi-monthly":
                month_diff = (d.year - start_date.year) * 12 + (d.month - start_date.month)
                if month_diff % 2 == 0 and d.day == cost['day']:
                    hit = True
            elif cost['freq'] == "quarterly" and d.day == cost['day'] and d.month in [3, 6, 9, 12]:
                hit = True

            if hit:
                if cost.get('use_cc', False):
                    loans[0]['bal'] += cost['amt']
                    outflows.append(f"{cost['desc']} (CC): -${cost['amt']:,.2f}")
                else:
                    bank_balance -= cost['amt']
                    outflows.append(f"{cost['desc']}: -${cost['amt']:,.2f}")

    # 4. Overdraft Prevention (Re-borrow from LOC)
    if bank_balance < 0:
        overdraft = abs(bank_balance)
        loans[1]['bal'] += overdraft
        inflows.append(f"LOC Float: +${overdraft:,.2f}")
        bank_balance = 0

    # 5. Interest & Repayment
    for l in sorted(loans, key=lambda x: x['rate'], reverse=True):
        if l['desc'] == "LOC":  # Only apply interest to LOC; CC is floated interest-free
            weekly_interest = round((l['bal'] * l['rate']) / 52, 2)
            l['bal'] += weekly_interest
            total_interest_paid += weekly_interest

        if bank_balance > min_bank_buffer and l['bal'] > 0:
            payment = min(bank_balance - min_bank_buffer, l['bal'])
            l['bal'] -= round(payment, 2)
            bank_balance -= round(payment, 2)
            outflows.append(f"Repay {l['desc']}: -${payment:,.2f}")

    data.append({
        "Date": week_start,
        "LOC": round(loans[1]['bal'], 2),
        "CC": round(loans[0]['bal'], 2),
        "Bank": round(bank_balance, 2),
        "Total Debt": round(sum(l['bal'] for l in loans), 2),
        "Cumulative Interest": round(total_interest_paid, 2),
        "Details": "<b>Weekly Detail:</b><br>" + "<br>".join(inflows + outflows)
    })
    current_date += timedelta(days=7)

# --- FIND ZERO DATE ---
df = pd.DataFrame(data)
zero_row = df[df['Total Debt'] <= 0.01].head(1)
if not zero_row.empty:
    zero_date_str = zero_row['Date'].iloc[0].strftime("%b %d, %Y")
    annotation_text = f"Debt Free Date: {zero_date_str}"
else:
    remaining = df['Total Debt'].iloc[-1]
    annotation_text = f"End Balance: ${remaining:,.2f}"

final_interest = df['Cumulative Interest'].iloc[-1]

# --- PLOT ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Total Debt'], name='Total Debt', hovertext=df['Details'], line=dict(color='firebrick', width=3)))
fig.add_trace(go.Scatter(x=df['Date'], y=df['Bank'], name='Bank Balance', line=dict(color='blue', width=1, dash='dot')))

# Floating Annotation for "Time to 0"
fig.add_annotation(
    x=df['Date'].iloc[len(df)//2], y=df['LOC'].max() * 0.9,
    text=f"<b>{annotation_text}</b>",
    showarrow=False, font=dict(size=16, color="darkgreen"),
    bgcolor="white", bordercolor="darkgreen", borderwidth=2, borderpad=4
)

fig.update_layout(
    title=f"Debt Pay-off Forecaster | Total Interest: ${final_interest:,.2f}",
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