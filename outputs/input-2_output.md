# Validation Report — `input-2.json`

**7 records checked — 2 passed, 5 failed.** Every record was evaluated; none were skipped.

## Run details

| Item | Value |
|---|---|
| Branch | `uddeshya-test` (HEAD `56f6716`) |
| Data file | `input-2.json` (repository root) |
| Validator | `customer_validator.py` (repository root) |
| Command | `python3 customer_validator.py input-2.json` (run from repo root) |
| Exit status | `0` — not a pass/fail signal; outcome read from the report text |

## Failures

| # | Customer | Why it failed |
|---|---|---|
| 2 | Priya Singh | Invalid email format: `priya.singhgmail.com` (no `@`) |
| 3 | Amit Verma | Phone must contain exactly 10 digits: `98765432` (8 digits) |
| 5 | *(blank name)* | Name cannot be empty |
| 6 | Sneha Patel | Age must be an integer, got `str` (`"twenty-five"`) |
| 7 | Arjun Mehta | Two problems: age must be between 0 and 120, got `145`; active must be `yes` or `no`, got `maybe` |

Passed: **Customer 1 (Rahul Sharma)** and **Customer 4 (Neha Kapoor)**.

Unevaluated records: **none**.

## Validator output (verbatim)

```

============================================================
             CUSTOMER VALIDATION REPORT
============================================================

Customer 1: VALID

Customer 2: INVALID
  - Invalid email format: 'priya.singhgmail.com'.

Customer 3: INVALID
  - Phone must contain exactly 10 digits: '98765432'.

Customer 4: VALID

Customer 5: INVALID
  - Name cannot be empty.

Customer 6: INVALID
  - Age must be an integer, got str.

Customer 7: INVALID
  - Age must be between 0 and 120, got 145.
  - Active must be either 'yes' or 'no', got 'maybe'.

------------------------------------------------------------
SUMMARY
------------------------------------------------------------
Total customers   : 7
Valid customers   : 2
Invalid customers : 5
============================================================
```

No data or validator files were changed by this run.
