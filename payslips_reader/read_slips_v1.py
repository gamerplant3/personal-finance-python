# library imports: pip install pymupdf pandas openpyxl
import os
import re
import fitz
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook

#FIX ME! LOTS OF BREAKAGES WHEN THE FILES ARE BIGGER! (more lines per section)

# folder containing PDF files
folder = r"C:\Users\wchikowero\Documents\Local\payslips\v1"

# functions for reading PDF files, extracting text, and writing to Excel
def extract_lines_from_pdf(file_path):
    with fitz.open(file_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return [line.strip() for line in text.splitlines() if line.strip()]

def text_to_number(s):
    try:
        return float(s.replace('$', '').replace(',', '').strip())
    except:
        return None

def text_to_date(s):
    s = s.strip()
    formats = [
        "%B %d, %Y",  # old payslips have May 8, 2021 format
        "%Y-%m-%d", # new payslips have 2021-05-08 format
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

# determine which payslip format the PDF is in
def detect_format(lines):
    # Old style "2" has "Printed on" and "Hrs/Units"
    if any("Printed on" in line for line in lines):
        return "old_style"
    if "Hrs/Units" in lines:
        return "old_style"

    # Default fallback to new style "1"
    return "new_style"

def parse_paystub(lines, filename):
    fmt = detect_format(lines)
    if fmt == "new_style":
        return parse_paystub_new(lines, filename)
    else:
        return parse_paystub_old(lines, filename)

# === NEW STYLE PAYSLIPS (all working, missing "pay rates") ===
def extract_earning_entries_new(lines, start_index, max_entries, stop_phrase):
    earnings = []
    current_line = start_index
    while current_line < len(lines):
        # merge multi-line description text until you find the first number
        description_lines = []
        while current_line < len(lines) and not re.match(r"^\d", lines[current_line]):
            if lines[current_line] == stop_phrase:
                    break # stop looking for entries when you hit this trigger word
            description_lines.append(lines[current_line])
            current_line += 1

        if not description_lines:
            break

        desc = " ".join(description_lines)

        try:
            hrs = text_to_number(lines[current_line])
            rate = ""
            amount = text_to_number(lines[current_line + 2])
            cumulative = text_to_number(lines[current_line + 3])
            current_line += 4
        except IndexError:
            break

        earnings.append([desc, hrs, rate, amount, cumulative])
        if len(earnings) >= max_entries:
            break
    return earnings

def extract_deduction_entries_new(lines, start_index, max_entries, stop_phrase):
    deductions = []
    current_line = start_index
    while current_line < len(lines):
        # merge multi-line description text until you find the first number
        description_lines = []
        while current_line < len(lines) and not re.match(r"^\d", lines[current_line]):
            if lines[current_line] == stop_phrase:
                break  # stop looking for entries when you hit this trigger word
            description_lines.append(lines[current_line])
            current_line += 1

        if not description_lines:
            break

        desc = " ".join(description_lines)

        try:
            amount = text_to_number(lines[current_line])
            cumulative = text_to_number(lines[current_line + 1])
            current_line += 2
        except IndexError:
            break

        deductions.append([desc, amount, cumulative])
        if len(deductions) >= max_entries:
            break
    return deductions

def extract_accruals_entries_new(lines, start_index, max_entries, stop_phrase):
    accruals = []
    current_line = start_index
    while current_line < len(lines):
        # merge multi-line description text until you find the first number
        description_lines = []
        while current_line < len(lines) and not re.match(r"^\d", lines[current_line]):
            if lines[current_line] == stop_phrase:
                break  # stop looking for entries when you hit this trigger word
            description_lines.append(lines[current_line])
            current_line += 1

        if not description_lines:
            break

        desc = " ".join(description_lines)

        try:
            amount = text_to_number(lines[current_line])
            cumulative = text_to_number(lines[current_line + 1])
            current_line += 2
        except IndexError:
            break

        accruals.append([desc, amount, cumulative])
        if len(accruals) >= max_entries:
            break
    return accruals

def extract_employer_entries_new(lines, start_index, max_entries, stop_phrase):
    employer_contributions = []
    current_line = start_index
    while current_line < len(lines):
        # merge multi-line description text until you find the first number
        description_lines = []
        while current_line < len(lines) and not re.match(r"^\d", lines[current_line]):
            if lines[current_line] == stop_phrase:
                    break # stop looking for entries when you hit this trigger word
            description_lines.append(lines[current_line])
            current_line += 1

        if not description_lines:
            break

        desc = " ".join(description_lines)

        try:
            hrs = text_to_number(lines[current_line])
            rate = text_to_number(lines[current_line + 1])
            amount = text_to_number(lines[current_line + 2])
            cumulative = text_to_number(lines[current_line + 3])
            current_line += 4
        except IndexError:
            break

        employer_contributions.append([desc, hrs, rate, amount, cumulative])
        if len(employer_contributions) >= max_entries:
            break
    return employer_contributions

def parse_paystub_new(lines, filename):
    data = {}
    max_entries = 10

    # === HEADER DATA ===
    data["File Name"] = filename
    data["Pay Cycle"] = text_to_number(lines[1].split(":")[1].strip())
    data["Pay Sequence"] = lines[2].split(":")[1].strip()
    data["Employer"] = lines[3].strip()
    data["Employer Address"] = " ".join(lines[4:8])
    data["Employee Name"] = lines[8].strip()
    data["Employee Address"] = " ".join(lines[9:12])
    data["Account"] = lines[15].strip()
    data["Net Pay"] = text_to_number(lines[14].strip().rstrip('$'))
    data["Employee ID"] = lines[17].strip().split()[0]
    data["Work Period Start"] = text_to_date(lines[21].strip().replace("From: ", ""))
    data["Work Period End"] = text_to_date(lines[22].strip().replace("To: ", ""))
    data["Employee Title"] = lines[20].strip()
    data["Pay Date"] = text_to_date(lines[23].strip())

    # === EARNINGS & REIMBURSEMENTS ===
    # start extracting earnings after the first "Cumul." line
    earnings_start = lines.index("Cumul.") + 1
    earnings = extract_earning_entries_new(lines, earnings_start, max_entries, stop_phrase="Description")

    for i in range(max_entries):
        if i < len(earnings):
            entry = earnings[i]
            data[f"EARNINGS - Description {i + 1}"] = entry[0]
            data[f"EARNINGS - Hrs {i + 1}"] = entry[1]
            data[f"EARNINGS - Rate {i + 1}"] = entry[2]
            data[f"EARNINGS - Amount {i + 1}"] = entry[3]
            data[f"EARNINGS - Cumul. {i + 1}"] = entry[4]
        else:
            data[f"EARNINGS - Description {i + 1}"] = ""
            data[f"EARNINGS - Hrs {i + 1}"] = ""
            data[f"EARNINGS - Rate {i + 1}"] = ""
            data[f"EARNINGS - Amount {i + 1}"] = ""
            data[f"EARNINGS - Cumul. {i + 1}"] = ""

    # === DEDUCTIONS ===
    # find the next Description tag after earnings, then skip to it's end (Cumul.)
    deductions_description_index = next(i for i in range(earnings_start, len(lines)) if lines[i] == "Description")
    deductions_header_index = next(i for i in range(deductions_description_index, len(lines)) if lines[i] == "Cumul.")
    deductions_start = deductions_header_index + 1
    deductions = extract_deduction_entries_new(lines, deductions_start, max_entries, stop_phrase="Description")

    for i in range(max_entries):
        if i < len(deductions):
            entry = deductions[i]
            data[f"DEDUCTIONS - Description {i+1}"] = entry[0]
            data[f"DEDUCTIONS - Amount {i+1}"] = entry[1]
            data[f"DEDUCTIONS - Cumul. {i+1}"] = entry[2]
        else:
            data[f"DEDUCTIONS - Description {i+1}"] = ""
            data[f"DEDUCTIONS - Amount {i+1}"] = ""
            data[f"DEDUCTIONS - Cumul. {i+1}"] = ""

    # === ACCRUALS ===
    # find the next Description tag after deductions, then skip to it's end (Cumul.)
    accruals_description_index = next(i for i in range(deductions_start, len(lines)) if lines[i] == "Description")
    accruals_header_index = next(i for i in range(accruals_description_index, len(lines)) if lines[i] == "Cumul.")
    accruals_start = accruals_header_index + 1
    accruals = extract_accruals_entries_new(lines, accruals_start, max_entries, stop_phrase="EI Hours")

    for i in range(max_entries):
        if i < len(accruals):
            entry = accruals[i]
            data[f"ACCRUALS - Description {i+1}"] = entry[0]
            data[f"ACCRUALS - Amount {i+1}"] = entry[1]
            data[f"ACCRUALS - Cumul. {i+1}"] = entry[2]
        else:
            data[f"ACCRUALS - Description {i+1}"] = ""
            data[f"ACCRUALS - Amount {i+1}"] = ""
            data[f"ACCRUALS - Cumul. {i+1}"] = ""

    # === EI HOURS ===
    current_line = accruals_start + len(accruals) + 1
    data["EI Hours"] = lines[current_line]

    # === EMPLOYER CONTRIBUTION ===
    # find the next Description tag after accruals, then skip to it's end (Cumul.)
    empcont_description_index = next(i for i in range(accruals_start, len(lines)) if lines[i] == "Description")
    empcont_header_index = next(i for i in range(empcont_description_index, len(lines)) if lines[i] == "Cumul.")
    empcont_start = empcont_header_index + 1
    employer_contributions = extract_employer_entries_new(lines, empcont_start, max_entries, stop_phrase="Description")

    for i in range(max_entries):
        if i < len(employer_contributions):
            entry = employer_contributions[i]
            data[f"EMPLOYER CONTRIBUTION - Description {i + 1}"] = entry[0]
            data[f"EMPLOYER CONTRIBUTION - Hrs {i + 1}"] = entry[1]
            data[f"EMPLOYER CONTRIBUTION - Rate {i + 1}"] = entry[2]
            data[f"EMPLOYER CONTRIBUTION - Amount {i + 1}"] = entry[3]
            data[f"EMPLOYER CONTRIBUTION - Cumul. {i + 1}"] = entry[4]
        else:
            data[f"EMPLOYER CONTRIBUTION - Description {i + 1}"] = ""
            data[f"EMPLOYER CONTRIBUTION - Hrs {i + 1}"] = ""
            data[f"EMPLOYER CONTRIBUTION - Rate {i + 1}"] = ""
            data[f"EMPLOYER CONTRIBUTION - Amount {i + 1}"] = ""
            data[f"EMPLOYER CONTRIBUTION - Cumul. {i + 1}"] = ""

    # === EMPLOYEE BENEFIT ===
    data["EMPLOYEE BENEFIT - Description"] = "not used"
    data["EMPLOYEE BENEFIT - Amount"] = "not used"
    data["EMPLOYEE BENEFIT - Cumul."] = "not used"

    return data

# === OLD STYLE PAYSLIPS (earnings fixed, deductions are in wrong order) ===
def extract_earning_entries_old(lines, start_index, max_entries, stop_phrase):
    earnings = []
    n_earnings = 0 # counting as we go along
    current_line = start_index

    # determine total earnings types by counting lines until stop_phrase
    total_earnings = 0 # overall
    for line in lines[current_line:]:
        if not re.match(r"^\d", line):
            total_earnings += 1 # only counting description lines
        elif line == stop_phrase:
            break

    # for some reason, cumulative earnings appear after the deductions block
    # which is marked by the stop_phrase Federal Tax. Skip words and numbers
    count_deductions_lines = 0
    federal_tax_index = next(i for i, line in enumerate(lines) if "Federal Tax" in line)
    for line in lines[federal_tax_index:]:
        if not re.match(r"^\d", line):
            count_deductions_lines += 1
        else:
            break  # stop at the first numeric line
    cumul_index = federal_tax_index + count_deductions_lines * 2  # skip both the headers and values

    while current_line < len(lines):
        if lines[current_line] == stop_phrase:
            break

        desc = lines[current_line] # no multi-line descriptions in the old PDFs
        rate = "" # old style does not have rate
        cumul = text_to_number(lines[cumul_index + n_earnings])

        if re.match(r"^\d", lines[current_line+1]):
            hrs = text_to_number(lines[current_line+1])
            amount = text_to_number(lines[current_line+2])
            current_line += 3
        else:
            # earning category doesn't have values
            hrs = ""
            amount = ""
            current_line += 1

        earnings.append([desc, hrs, rate, amount, cumul])
        n_earnings += 1
        if len(earnings) >= max_entries:
            break

    return earnings

def extract_deduction_entries_old(lines, start_index, n_earnings, max_entries):
    deductions = []
    current_line = start_index
    n_deductions = 0

    # deductions have n lines of descriptions then n lines of values
    count_deductions_lines = 0
    federal_tax_index = next(i for i, line in enumerate(lines) if "Federal Tax" in line)
    for line in lines[current_line:]:
        if not re.match(r"^\d", line): count_deductions_lines += 1
        else: break  # stop at the first numeric line
    cumul_index = federal_tax_index + count_deductions_lines * 2  # skip both the headers and values

    while current_line < len(lines):
        desc = lines[current_line]
        try:
            amount = text_to_number(lines[current_line + count_deductions_lines])
            cumul = text_to_number(lines[cumul_index + n_earnings + n_deductions])
            current_line += 1
        except IndexError:
            break

        deductions.append([desc, amount, cumul])
        n_deductions += 1

        if len(deductions) >= count_deductions_lines or len(deductions) >= max_entries:
            break

    return deductions

def extract_accrual_entries_old(max_entries):
    # old style does not have accrual entries
    return [i for i in range(max_entries)]

def extract_employer_entries_old(lines, max_entries, start_index):
    employer = []
    i = start_index

    for _ in range(max_entries):
        if i + 4 >= len(lines):
            break

        desc = lines[i]
        try:
            hrs  = text_to_number(lines[i+1])
            rate = text_to_number(lines[i+2])
            amount = text_to_number(lines[i+3])
            cumul = text_to_number(lines[i+4])
        except IndexError:
            break

        employer.append([desc, hrs, rate, amount, cumul])
        i += 5

    return employer

def parse_paystub_old(lines, filename):
    data = {}
    max_entries = 10
    EI_hours_index = next(i for i, line in enumerate(lines) if "EI Hours" in line)
    Printed_index = next(i for i, line in enumerate(lines) if "Printed on" in line)

    # === HEADER DATA ===
    data["File Name"] = filename
    data["Employee Name"] = lines[11]
    data["Employee Title"] = lines[EI_hours_index + 1]
    data["Employee ID"] = lines[EI_hours_index + 2].split(" ",1)[0]
    data["Employer"] = lines[Printed_index - 1]
    data["Account"] = lines[EI_hours_index + 11]
    data["Net Pay"] = text_to_number(lines[EI_hours_index + 12])
    data["Work Period Start"] = text_to_date(lines[EI_hours_index + 3].strip())
    data["Work Period End"] = text_to_date(lines[EI_hours_index + 7].strip())
    data["Pay Date"] = text_to_date(lines[EI_hours_index + 6].strip())
    data["Employee Address"] = " ".join(lines[Printed_index - 7:Printed_index - 4])
    data["Employer Address"] = " ".join(lines[Printed_index - 4:Printed_index - 1])

    # === EARNINGS ===
    earnings_start = 17
    earnings = extract_earning_entries_old(lines, earnings_start, max_entries, stop_phrase="Federal Tax")
    for i in range(max_entries):
        if i < len(earnings):
            desc, hrs, rate, amount, cumul = earnings[i]
        else:
            desc = hrs = rate = amount = cumul = ""
        data[f"EARNINGS - Description {i+1}"] = desc
        data[f"EARNINGS - Hrs {i+1}"] = hrs
        data[f"EARNINGS - Rate {i+1}"] = rate
        data[f"EARNINGS - Amount {i+1}"] = amount
        data[f"EARNINGS - Cumul. {i+1}"] = cumul

    # === DEDUCTIONS ===
    deductions_start = next((i for i, l in enumerate(lines) if l.lower() == "federal tax"), None)
    if deductions_start is not None:
        deductions = extract_deduction_entries_old(lines, deductions_start, len(earnings), max_entries)
    else:
        deductions = []
    for i in range(max_entries):
        if i < len(deductions):
            desc, amount, cumul = deductions[i]
        else:
            desc = amount = cumul = ""
        data[f"DEDUCTIONS - Description {i+1}"] = desc
        data[f"DEDUCTIONS - Amount {i+1}"] = amount
        data[f"DEDUCTIONS - Cumul. {i+1}"] = cumul

    # === ACCRUALS ===
    accruals = extract_accrual_entries_old(max_entries)
    for i in range(max_entries):
        data[f"ACCRUALS - Description {i+1}"] = accruals[i]
        data[f"ACCRUALS - Amount {i+1}"] = accruals[i]
        data[f"ACCRUALS - Cumul. {i+1}"] = accruals[i]

    # === EMPLOYER CONTRIBUTIONS ===
    emp_start = next((i for i, l in enumerate(lines) if l == "EMPLOYER CONTRIBUTIONS"), None)
    if emp_start is not None:
        employer_contributions = extract_employer_entries_old(lines, emp_start, max_entries)
    else:
        employer_contributions = []
    for i in range(max_entries):
        if i < len(employer_contributions):
            desc, hrs, rate, amount, cumul = employer_contributions[i]
        else:
            desc = hrs = rate = amount = cumul = ""
        data[f"EMPLOYER CONTRIBUTION - Description {i+1}"] = desc
        data[f"EMPLOYER CONTRIBUTION - Hrs {i+1}"] = hrs
        data[f"EMPLOYER CONTRIBUTION - Rate {i+1}"] = rate
        data[f"EMPLOYER CONTRIBUTION - Amount {i+1}"] = amount
        data[f"EMPLOYER CONTRIBUTION - Cumul. {i+1}"] = cumul

    # === EMPLOYEE BENEFIT ===
    data["EMPLOYEE BENEFIT - Description"] = "not used"
    data["EMPLOYEE BENEFIT - Amount"] = "not used"
    data["EMPLOYEE BENEFIT - Cumul."] = "not used"

    return data

# write data to Excel
def write_to_excel(data_rows, output_file, sheet_name):
    columns = list(data_rows[0].keys()) # Use the dictionary keys as the column names

    df = pd.DataFrame(data_rows)
    df = df.reindex(columns=columns)  # Keep consistent order

    if os.path.exists(output_file):
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

# process each PDF in the folder
results = []

for filename in os.listdir(folder):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(folder, filename)
        lines = extract_lines_from_pdf(pdf_path)
        result = parse_paystub(lines, filename)
        results.append(result)

        # troubleshooting: Run one file only and print raw and structured data
        #print(f"\n=== Raw extracted lines from: {filename} ===")
        #for i, line in enumerate(lines): print(f"{i:02}: {line}")
        #print(f"\n=== Structured data from: {filename} ===")
        #for key, value in result.items(): print(f"{key:45}: {value}")
        #break

output_path = os.path.join(folder, "pay_summary.xlsx")
write_to_excel(results, output_path, sheet_name="Raw Data")
print(f"\n✅ Saved to: {output_path}")
