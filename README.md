| file | description |
| :--- | :--- |
| analyze_directory.py | given a directory, returns count of filetypes contained in that folder and total file sizes |
| balance_at_maturity.py | given current date, mortgage balance, and maturity date, returns the remaining principal balance at end of term |
| prepayment_analysis.py | given mortgage balance and terms, simulates various prepayment scenarios and effect of different frequencies |
| cashflow_2026.py | determines weekly cashflow for a given timeframe given list of income and expenses to determine debt payoff |
| cashflow_2026_streamlit.py | streamlit version of cashflow_2026.py |

**output from cashflow_2026_streamlit.py**
<img width="2233" height="1286" alt="Screenshot 2026-02-06 002431" src="https://github.com/user-attachments/assets/f29106a3-50e0-45f0-b8d7-2598af8902e8" />

<img width="1787" height="910" alt="Screenshot 2026-02-07 135104" src="https://github.com/user-attachments/assets/1d51bc62-4383-49c6-8fd6-64cbdf758f4c" />

**output from cashflow_2026.py**
<img width="2198" height="1313" alt="Screenshot 2026-02-03 214913" src="https://github.com/user-attachments/assets/9e240b73-807f-448f-96b9-9d8ea152fec6" />

**output from prepayment_analysis.py**
```
--- TABLE 1: MONTHLY PAYMENTS OVER 5 YRS ($1,787.77) ---
Extra   Freq Prepayments Principal Paid Interest Saved Balance at Renewal
   $0 Weekly       $0.00     $47,110.62          $0.00        $303,879.03
 $100 Weekly  $26,000.00     $75,595.53      $2,484.91        $275,394.12
 $150 Weekly  $39,000.00     $89,837.98      $3,727.36        $261,151.67
 $200 Weekly  $52,000.00    $104,080.43      $4,969.81        $246,909.22
 $250 Weekly  $65,000.00    $118,322.88      $6,212.26        $232,666.77

--- TABLE 2: ACCELERATED WEEKLY PAYMENTS OVER 5 YRS ($446.94) ---
Extra   Freq Prepayments Principal Paid Saved by Freq Saved by Prepay Total Int Saved Balance at Renewal
   $0 Weekly       $0.00     $57,052.41     $1,003.59           $0.00       $1,003.59        $293,937.24
 $100 Weekly  $26,000.00     $85,570.72     $1,003.59       $2,518.31       $3,521.90        $265,418.93
 $150 Weekly  $39,000.00     $99,829.88     $1,003.59       $3,777.47       $4,781.06        $251,159.77
 $200 Weekly  $52,000.00    $114,089.04     $1,003.59       $5,036.63       $6,040.22        $236,900.61
 $250 Weekly  $65,000.00    $128,348.19     $1,003.59       $6,295.78       $7,299.37        $222,641.46
```

**output from balance_at_maturity.py**
```
Today is: 2026-01-14
Principal after last payment (Mar 26): $350,711.58
Accrued interest (6 days till maturity): $278.07
Balance at Maturity (Apr 1): $350,989.65
```

**output figure from analyze_directory.py**
![image](https://github.com/user-attachments/assets/53668afe-28b1-4136-9f71-d64562285d6e)






