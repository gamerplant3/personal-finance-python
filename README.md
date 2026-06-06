# personal-finance-python

Personal finance modeling tools focused on mortgage math (Canadian), debt pay-off simulation, and cashflow forecasting.

## Quick start

```bash
pip install -r requirements.txt
streamlit run streamlit_app/Home.py
```

## Project structure

| file / folder | description |
| :--- | :--- |
| `mortgage_math.py` | Canadian semi-annual compounding, prepayment scenarios, balance at maturity; shared default scenario constants (`DEFAULT_PRINCIPAL`, rate, amortization, term, prepayment extras) used by CLI, Streamlit, and tests |
| `cashflow_engine.py` | Weekly cashflow simulation (CC float, LOC cover, debt strategies) |
| `streamlit_app/Home.py` | Multi-page dashboard entry point |
| `streamlit_app/pages/cashflow.py` | Debt pay-off forecaster with scenario compare and sensitivity |
| `streamlit_app/pages/mortgage_prepayment.py` | Shared mortgage profile editor; balance at maturity and interest-over-term metrics; prepayment scenario tables and charts |
| `streamlit_app/components/mortgage_profile.py` | Session-state mortgage parameters for the Prepayment page; read-only summary on Cashflow |
| `streamlit_app/components/session_state.py` | Cashflow config and sidebar widget persistence across page navigation and reruns |
| `prepayment_analysis.py` | CLI prepayment tables |
| `random_unrelated/` | Unrelated utility scripts (payslip PDF extraction, Revit/Dynamo helpers, directory tools); not part of the finance app |

## Dashboard pages

1. **Cashflow and Debt Forecaster** - weekly cashflow and debt payoff simulation; edit debts, expenses, and windfalls; compare scenarios and run sensitivity sliders; save/load JSON
2. **Mortgage Prepayment** - edit shared mortgage profile; prepayment scenario tables (monthly and accelerated weekly); balance and interest charts

## CLI scripts

```bash
python mortgage_math.py          # balance at maturity
python prepayment_analysis.py    # prepayment comparison tables
```

Cashflow forecasting is available via the Streamlit dashboard (`streamlit run streamlit_app/Home.py`) or by importing `cashflow_engine.run_cashflow_simulation` directly.

## Tests

```bash
python -m pytest tests/ -v
```

## Screenshots

**output from cashflow forecaster (Streamlit)**

Page 1

<img width="2600" height="4400" alt="screenie" src="https://github.com/user-attachments/assets/ac3d9717-5516-4c8c-824b-129b49a4794b" />

Page 2

<img width="2600" height="4400" alt="2ndscreenie" src="https://github.com/user-attachments/assets/63c8997c-7fac-4d00-8f5b-4864d74474d5" />

**output from prepayment_analysis.py** (defaults: $350k principal, 3.7% rate, 25-yr amort, 5-yr term)

```
--- TABLE 1: MONTHLY PAYMENTS OVER 5 YRS ($1,784.60) ---
    Extra Prepayments Principal Paid Interest Saved Balance at Renewal
    $0.00       $0.00     $46,923.62          $0.00        $303,076.38
  $400.00  $24,000.00     $75,415.61      $2,491.99        $274,584.39
  $600.00  $36,000.00     $89,661.61      $3,737.99        $260,338.39
  $800.00  $48,000.00    $103,907.60      $4,983.98        $246,092.40
$1,000.00  $60,000.00    $118,153.60      $6,229.98        $231,846.40

--- TABLE 2: ACCELERATED WEEKLY PAYMENTS OVER 5 YRS ($446.15) ---
Extra Prepayments Principal Paid Saved by Prepay Total Int Saved Balance at Renewal
   $0       $0.00     $56,851.36           $0.00       $1,004.74        $293,148.64
 $100  $26,000.00     $85,376.86       $2,525.50       $3,530.24        $264,623.14
 $150  $39,000.00     $99,639.61       $3,788.25       $4,792.99        $250,360.39
 $200  $52,000.00    $113,902.36       $5,051.00       $6,055.74        $236,097.64
 $250  $65,000.00    $128,165.11       $6,313.75       $7,318.49        $221,834.89
```

**output from mortgage_math.py** (defaults: $350k principal, 3.7% rate; $446.15/wk accelerated payment, maturity Apr 1 2026)

```
Principal after last payment (Mar 26): $347,799.95
Accrued interest (6 days till maturity): $209.67
Balance at Maturity (Apr 1): $348,009.62
```
