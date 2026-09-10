# Customer Validation Report — input-2.json

**7 records checked: 2 passed, 5 failed.**

- Branch: `uddeshya-test`
- Data file: `input-2.json` (repository root)
- Command: `python3 customer_validator.py input-2.json`
- Exit status: 0 (the validator exits 0 even when records fail — the outcome above is read from the report text)
- Records the validator could not evaluate: none

## Failures

| # | Name | Problem |
|---|------|---------|
| 2 | Priya Singh | Email is missing the `@` — `priya.singhgmail.com` |
| 3 | Amit Verma | Phone has 8 digits, needs exactly 10 — `98765432` |
| 5 | (blank) | Name is empty |
| 6 | Sneha Patel | Age is text (`"twenty-five"`), needs a whole number |
| 7 | Arjun Mehta | Age 145 is outside 0–120, and `active` is `maybe` (must be `yes` or `no`) |

Passed: record 1 (Rahul Sharma) and record 4 (Neha Kapoor).

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

## Export

Pending approval — see the Export Report to Branch stage.
