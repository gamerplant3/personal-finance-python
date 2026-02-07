# streamlit version of cashflow_2026.py which allows user to change inputs
# run in terminal: streamlit run cashflow_2026_streamlit.py

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
import streamlit as st
from datetime import datetime, timedelta

# --- UI CONFIGURATION & CSS OVERHAUL ---
st.set_page_config(page_title="Forecaster", layout="wide")

st.markdown("""
    <style>
    /* Page Title */
    h1 { 
        font-size: 1.8rem !important; 
        margin-bottom: 0.5rem; 
    }

    /* Section headers */
    h3 {
        font-size: 1rem !important;
        font-weight: 700 !important;
        color: #4FACFE !important;
        text-transform: uppercase !important;
    }

    /* Vertical spacing */
    .stNumberInput {margin-bottom: -10px;}
    .stSelectbox {margin-bottom: -10px;}
    .stDateInput {margin-bottom: -10px;}
    
    /* Align checkbox with inputs */
    div[data-testid="stCheckbox"] {
        margin-top: 32px !important;
    }
    
    hr {margin-top: 1rem; margin-bottom: 1rem; border-color: #444;}
    </style>
    """, unsafe_allow_html=True)

st.title("Debt Pay-off Forecaster")

FREQUENCIES = ["weekly", "bi-weekly", "monthly", "bi-monthly", "quarterly"]

with st.sidebar:
    # --- 1. INCOME ---
    st.subheader("💰 Income")
    b1, b2 = st.columns([1, 1])
    bank_balance = b1.number_input("Starting Bank Balance ($)", value=0.0, step=100.0)
    min_bank_buffer = b2.number_input("Min. Balance ($)", value=100.0, step=50.0)

    c1, c2 = st.columns([1, 1])
    start_date_ui = c1.date_input("Start Date", value=datetime(2026, 2, 3))
    end_date_ui = c2.date_input("End Date", value=datetime(2026, 12, 31))

    c3, c4 = st.columns([1, 1])
    income_biweekly = c3.number_input("Bi-weekly Net Income ($)", value=2500.0, step=100.0)
    next_pay_ui = c4.date_input("Next Pay Date", value=datetime(2026, 2, 13))

    w1, w2 = st.columns([1, 1])
    wf_amt = w1.number_input("Bonus ($)", value=5000.0, step=100.0, key="wf_a")
    wf_date = w2.date_input("Date", value=datetime(2026, 4, 15), key="wf_d")

    st.divider()

    # --- 2. EXPENSES ---
    TOOLTIP = "Amount - Frequency - Paid with Credit?"
    st.subheader("🏠 Expenses", help=TOOLTIP)

    l1, l2, l3 = st.columns([3, 2.5, 0.5])
    living_amt = l1.number_input("Living Expense ($)", value=250.0, step=50.0)
    living_freq = l2.selectbox("", FREQUENCIES, index=0)
    living_cc = l3.checkbox("", value=True, key="l_cc")

    h1, h2, h3 = st.columns([3, 2.5, 0.5])
    mort_amt = h1.number_input("Mortgage ($)", value=495.0, step=50.0, key="m_a")
    mort_freq = h2.selectbox("", FREQUENCIES, index=0, key="m_f")
    mort_cc = h3.checkbox("", value=False, key="m_cc")

    h4, h5, h6 = st.columns([3, 2.5, 0.5])
    condo_amt = h4.number_input("Condo Fees ($)", value=960.0, step=50.0, key="c_a")
    condo_freq = h5.selectbox("", FREQUENCIES, index=2, key="c_f")
    condo_cc = h6.checkbox("", value=False, key="c_cc")

    h7, h8, h9 = st.columns([3, 2.5, 0.5])
    ins_amt = h7.number_input("Home Insurance ($)", value=80.0, step=10.0, key="i_a")
    ins_freq = h8.selectbox("", FREQUENCIES, index=2, key="i_f")
    ins_cc = h9.checkbox("", value=True, key="i_cc")

    h10, h11, h12 = st.columns([3, 2.5, 0.5])
    tax_amt = h10.number_input("Property Tax ($)", value=450.0, step=50.0, key="t_a")
    tax_freq = h11.selectbox("", FREQUENCIES, index=3, key="t_f")
    tax_cc = h12.checkbox("", value=False, key="t_cc")
    st.divider()

    # --- 3. DEBTS ---
    st.subheader("💳 Liabilities")

    d1, d2 = st.columns(2)
    cc_bal = d1.number_input("Credit Card", value=4000.0, step=100.0, key="cc_b")
    cc_rate = d2.number_input("APR %", value=21.99, step=1.0, key="cc_r") / 100

    d3, d4 = st.columns(2)
    loc_bal = d3.number_input("Line of Credit", value=15000.0, step=1000.0, key="loc_b")
    loc_rate = d4.number_input("APR %", value=5.45, step=0.05, key="loc_r") / 100

    cc_due_ui = st.date_input("Next CC Due Date", value=datetime(2026, 2, 9))

# --- SIMULATION ENGINE ---
start_date = datetime.combine(start_date_ui, datetime.min.time())
end_date = datetime.combine(end_date_ui, datetime.min.time())
next_pay_date = datetime.combine(next_pay_ui, datetime.min.time())
first_cc_due = datetime.combine(cc_due_ui, datetime.min.time())

number_of_weeks = max(1, ((end_date - start_date).days // 7) + 1)

loans = [
    {"desc": "Credit Card", "bal": float(cc_bal), "rate": cc_rate, "due_day": first_cc_due.day},
    {"desc": "LOC", "bal": float(loc_bal), "rate": loc_rate}
]

# mortgage on thursdays
housing_inputs = [
    {"desc": "Living Expense", "amt": living_amt, "freq": living_freq, "day": start_date.weekday(), "use_cc": living_cc},
    {"desc": "Mortgage", "amt": mort_amt, "freq": mort_freq, "day": 3, "use_cc": mort_cc},
    {"desc": "Condo Fees", "amt": condo_amt, "freq": condo_freq, "day": 1, "use_cc": condo_cc},
    {"desc": "Home Insurance", "amt": ins_amt, "freq": ins_freq, "day": 1, "use_cc": ins_cc},
    {"desc": "Property Tax", "amt": tax_amt, "freq": tax_freq, "day": 1, "use_cc": tax_cc}
]

data = []
current_date = start_date
sim_bank_balance = float(bank_balance)
total_interest_paid = 0.0
windfalls = [{"desc": "Bonus", "amt": wf_amt, "date": datetime.combine(wf_date, datetime.min.time())}]
payment_table_data = []

for week in range(number_of_weeks):
    week_start, week_end = current_date, current_date + timedelta(days=6)
    inflows, outflows = [], []

    # --- PRE-CALCULATE WEEKLY TOTALS FOR TABLE ---
    weekly_income_total = 0.0
    weekly_expense_total = 0.0
    for i in range(7):
        d = week_start + timedelta(days=i)
        if d > end_date: break

        if (d - next_pay_date).days % 14 == 0 and d >= next_pay_date:
            weekly_income_total += income_biweekly
        for w in windfalls:
            if d.date() == w['date'].date():
                weekly_income_total += w['amt']

        for cost in housing_inputs:
            hit = False
            if cost['freq'] == "weekly" and d.weekday() == cost['day']:
                hit = True
            elif cost['freq'] == "bi-weekly" and (d - start_date).days % 14 == 0:
                hit = True
            elif cost['freq'] == "monthly" and d.day == cost['day']:
                hit = True
            elif cost['freq'] == "bi-monthly":
                month_diff = (d.year - start_date.year) * 12 + (d.month - start_date.month)
                if month_diff % 2 == 0 and d.day == cost['day']: hit = True
            elif cost['freq'] == "quarterly" and d.day == cost['day'] and d.month in [3, 6, 9, 12]:
                hit = True
            if hit: weekly_expense_total += cost['amt']

    payment_made_this_week = False

    # daily tracking
    for i in range(7):
        d = week_start + timedelta(days=i)
        if d > end_date: break

        # Income
        if (d - next_pay_date).days % 14 == 0 and d >= next_pay_date:
            sim_bank_balance += income_biweekly
            inflows.append(f"Pay: +${income_biweekly:,.2f}")

        # Windfall
        for w in windfalls:
            if d.date() == w['date'].date():
                sim_bank_balance += w['amt']
                inflows.append(f"Bonus: +${w['amt']:,.2f}")

        # Expenses
        for cost in housing_inputs:
            hit = False
            if cost['freq'] == "weekly" and d.weekday() == cost['day']:
                hit = True
            elif cost['freq'] == "bi-weekly" and (d - start_date).days % 14 == 0:
                hit = True
            elif cost['freq'] == "monthly" and d.day == cost['day']:
                hit = True
            elif cost['freq'] == "bi-monthly":
                month_diff = (d.year - start_date.year) * 12 + (d.month - start_date.month)
                if month_diff % 2 == 0 and d.day == cost['day']: hit = True
            elif cost['freq'] == "quarterly" and d.day == cost['day'] and d.month in [3, 6, 9, 12]:
                hit = True

            if hit:
                if cost['use_cc']:
                    # Straight to CC (Floats until due date)
                    loans[0]['bal'] += cost['amt']
                    outflows.append(f"{cost['desc']} (CC): -${cost['amt']:,.2f}")
                else:
                    # Check if paying this expense would drop the bank below the minimum buffer
                    if (sim_bank_balance - cost['amt']) < min_bank_buffer:
                        available_above_buffer = max(0, sim_bank_balance - min_bank_buffer)
                        needed = cost['amt'] - available_above_buffer
                        loans[1]['bal'] += needed
                        sim_bank_balance += needed
                        outflows.append(f"LOC Float: +${needed:,.2f}")

                        # Table Entry
                        payment_table_data.append({
                            "Week": week_start.strftime('%Y-%m-%d'),
                            "Income": f"${weekly_income_total:,.2f}",
                            "Expenses": f"${weekly_expense_total:,.2f}",
                            "Source Account": "Line of Credit",
                            "Source Balance": f"${loans[1]['bal']:,.2f}",
                            "Destination": f"{cost['desc']} (LOC Cover)",
                            "Dest. Balance": "",
                            "Amount to Pay": f"${needed:,.2f}"
                        })
                        payment_made_this_week = True
                    else:
                        # if bank balance is sufficient to cover cost without hitting buffer
                        payment_table_data.append({
                            "Week": week_start.strftime('%Y-%m-%d'),
                            "Income": f"${weekly_income_total:,.2f}",
                            "Expenses": f"${weekly_expense_total:,.2f}",
                            "Source Account": "Bank Account",
                            "Source Balance": f"${sim_bank_balance:,.2f}",
                            "Destination": f"{cost['desc']}",
                            "Dest. Balance": "",
                            "Amount to Pay": f"${cost['amt']:,.2f}"
                        })
                        payment_made_this_week = True

                    sim_bank_balance -= cost['amt']
                    outflows.append(f"{cost['desc']}: -${cost['amt']:,.2f}")

        # CC payment on due date
        if d.day == loans[0]['due_day']:
            if loans[0]['bal'] > 0:
                payment_needed = loans[0]['bal']

                # Bank pays what it can
                bank_contribution = max(0.0, min(sim_bank_balance - min_bank_buffer, payment_needed))
                if bank_contribution > 0:
                    payment_table_data.append({
                        "Week": week_start.strftime('%Y-%m-%d'),
                        "Income": f"${weekly_income_total:,.2f}",
                        "Expenses": f"${weekly_expense_total:,.2f}",
                        "Source Account": "Bank Account",
                        "Source Balance": f"${sim_bank_balance:,.2f}",
                        "Destination": "Credit Card",
                        "Dest. Balance": f"${loans[0]['bal']:,.2f}",
                        "Amount to Pay": f"${bank_contribution:,.2f}"
                    })
                    sim_bank_balance -= bank_contribution
                    payment_made_this_week = True

                # Remaining payment is covered by LOC
                loc_contribution = payment_needed - bank_contribution
                if loc_contribution > 0:
                    payment_table_data.append({
                        "Week": week_start.strftime('%Y-%m-%d'),
                        "Income": f"${weekly_income_total:,.2f}",
                        "Expenses": f"${weekly_expense_total:,.2f}",
                        "Source Account": "Line of Credit",
                        "Source Balance": f"${loans[1]['bal']:,.2f}",
                        "Destination": "Credit Card",
                        "Dest. Balance": f"${loans[0]['bal'] - bank_contribution:,.2f}",
                        "Amount to Pay": f"${loc_contribution:,.2f}"
                    })
                    loans[1]['bal'] += loc_contribution
                    outflows.append(f"LOC Float (CC): +${loc_contribution:,.2f}")
                    payment_made_this_week = True

                outflows.append(f"CC Payment: -${payment_needed:,.2f}")
                loans[0]['bal'] = 0

    # LOC interest charges and payments
    for l in sorted(loans, key=lambda x: x['rate'], reverse=True):
        if l['desc'] == "LOC":
            weekly_interest = round((l['bal'] * l['rate']) / 52, 2) # weekly interest
            l['bal'] += weekly_interest
            total_interest_paid += weekly_interest

        # Apply any extra cash to LOC balance
        if l['desc'] == "LOC" and sim_bank_balance > min_bank_buffer and l['bal'] > 0:
            payment = min(sim_bank_balance - min_bank_buffer, l['bal'])

            # when LOC is paid off, stop making table entries
            if payment > 0.01:
                l['bal'] -= round(payment, 2)
                sim_bank_balance -= round(payment, 2)
                outflows.append(f"Paid {l['desc']}: -${payment:,.2f}")
                payment_made_this_week = True

                payment_table_data.append({
                    "Week": week_start.strftime('%Y-%m-%d'),
                    "Income": f"${weekly_income_total:,.2f}",
                    "Expenses": f"${weekly_expense_total:,.2f}",
                    "Source Account": "Bank Account",
                    "Source Balance": f"${sim_bank_balance:,.2f}",
                    "Destination": "LOC",
                    "Dest. Balance": f"${l['bal']:,.2f}",
                    "Amount to Pay": f"${payment:,.2f}"
                })

    # --- Log all weeks, including ones with no payments in them ---
    if not payment_made_this_week:
        payment_table_data.append({
            "Week": week_start.strftime('%Y-%m-%d'),
            "Income": f"${weekly_income_total:,.2f}",
            "Expenses": f"${weekly_expense_total:,.2f}",
            "Source Account": "Bank Account",
            "Source Balance": f"${sim_bank_balance:,.2f}",
            "Destination": "",
            "Dest. Balance": "",
            "Amount to Pay": "$0.00"
        })

    data.append({
        "Date": week_start,
        "Total Debt": round(sum(l['bal'] for l in loans), 2),
        "CC Balance": round(loans[0]['bal'], 2),
        "LOC Balance": round(loans[1]['bal'], 2),
        "Bank": round(sim_bank_balance, 2),
        "Cumulative Interest": round(total_interest_paid, 2),
        "Details": "<b>Weekly Detail:</b><br>" + "<br>".join(inflows + outflows)
    })
    current_date += timedelta(days=7)

# --- VISUALIZATION ---
df = pd.DataFrame(data)
zero_row = df[df['Total Debt'] <= 0.01].head(1)
annotation_text = f"Debt Free Date: {zero_row['Date'].iloc[0].strftime('%b %d, %Y')}" if not zero_row.empty else f"End Balance: ${df['Total Debt'].iloc[-1]:,.2f}"
final_interest = df['Cumulative Interest'].iloc[-1]

fig = go.Figure()
# Total Debt
fig.add_trace(go.Scatter(x=df['Date'], y=df['Total Debt'], name='Total Debt', hovertext=df['Details'],
                         line=dict(color='#FF4B4B', width=1)))
# CC Balance
fig.add_trace(go.Scatter(x=df['Date'], y=df['CC Balance'], name='CC Balance',
                         line=dict(color='#FFA500', width=2, dash='dash')))
# LOC Balance
fig.add_trace(go.Scatter(x=df['Date'], y=df['LOC Balance'], name='LOC Balance',
                         line=dict(color='#9370DB', width=2, dash='dash')))
# Bank Balance
fig.add_trace(go.Scatter(x=df['Date'], y=df['Bank'], name='Bank Balance',
                         line=dict(color='#00D1FF', width=2, dash='dot')))

fig.update_layout(
    title=f"Projection | {annotation_text} | Total Interest Paid: ${final_interest:,.2f}",
    hovermode="x unified",
    template="plotly_dark",
    yaxis=dict(title="Balance ($)", tickformat="$,.2f"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# --- Table of Weekly Inflows and Outflows ---
st.subheader("Weekly Cash Flow")

if payment_table_data:
    pay_df = pd.DataFrame(payment_table_data)

    # only label the first entry for a given week
    mask = pay_df['Week'].duplicated()
    pay_df.loc[mask, ["Week", "Income", "Expenses"]] = ""

    st.dataframe(
        pay_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Week": st.column_config.TextColumn("Week"),
            "Income": st.column_config.TextColumn("Income"),
            "Expenses": st.column_config.TextColumn("Expenses"),
            "Source Account": st.column_config.TextColumn("Source Account"),
            "Source Balance": st.column_config.TextColumn("Source Balance"),
            "Destination": st.column_config.TextColumn("Destination"),
            "Dest. Balance": st.column_config.TextColumn("Dest. Balance"),
            "Amount to Pay": st.column_config.TextColumn("Amount to Pay"),
        }
    )
else:
    st.info("No payments required for this period.")