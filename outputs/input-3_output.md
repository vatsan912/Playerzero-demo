# Validation Report — input-3.json

**10 records checked — 5 passed, 5 failed.**

| Item | Value |
|---|---|
| Repo / branch | `Playerzero-demo` / `uddeshya-test` (HEAD `b59102d`) |
| Data file | `input-3.json` (repo root, uncommitted upload) |
| Command | `python3 customer_validator.py input-3.json` (run from repo root) |
| Records skipped / unevaluable | None — all 10 were evaluated |

## Failures

| # | Customer | Reason given by the validator |
|---|---|---|
| 5 | Rohan Desai | Invalid email format: `rohan.desai@gmail` |
| 6 | Pooja Nair | Phone must contain exactly 10 digits: `985678903` |
| 7 | Siddharth Rao | Age must be an integer, got str |
| 8 | Tanya Kapoor | Age must be between 0 and 120, got 130 |
| 9 | Aditya Sharma | Active must be either `yes` or `no`, got `maybe` |

Each failing record has exactly one problem. Records 1–4 and 10 passed with no issues.

## Verbatim validator output

```
============================================================
             CUSTOMER VALIDATION REPORT
============================================================

Customer 1: VALID

Customer 2: VALID

Customer 3: VALID

Customer 4: VALID

Customer 5: INVALID
  - Invalid email format: 'rohan.desai@gmail'.

Customer 6: INVALID
  - Phone must contain exactly 10 digits: '985678903'.

Customer 7: INVALID
  - Age must be an integer, got str.

Customer 8: INVALID
  - Age must be between 0 and 120, got 130.

Customer 9: INVALID
  - Active must be either 'yes' or 'no', got 'maybe'.

Customer 10: VALID

------------------------------------------------------------
SUMMARY
------------------------------------------------------------
Total customers   : 10
Valid customers   : 5
Invalid customers : 5
============================================================
```

Raw capture: `input-3-raw-output.txt`. Process exit status was 0 and was not used to judge pass/fail.

No data file or validator code was changed.
