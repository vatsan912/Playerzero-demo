# CSV Data-Quality Validator

`validate_csv.py` validates a CSV file against data-quality rules declared in a JSON config
and reports every invalid record. Python 3 standard library only — no dependencies.

## Usage

```bash
python3 validate_csv.py examples/employees.csv -c examples/rules.employees.json
python3 validate_csv.py data.csv -c rules.json -f json -o report.json --fail-on-error
python3 validate_csv.py data.csv -c rules.json -f csv -o violations.csv
```

### Options

| Option | Description |
| --- | --- |
| `-c, --config` | JSON rules file (required) |
| `-f, --format` | `text` (default), `json`, or `csv` |
| `-o, --output` | Write the report to a file instead of stdout |
| `-d, --delimiter` | Override the delimiter from the config |
| `-e, --encoding` | Input encoding, default `utf-8-sig` (plain UTF-8 plus an optional byte-order mark) |
| `--max-records` | Cap invalid records listed in the text report (`0` = all, default 50) |
| `--fail-on-error` | Exit `1` when any violation is found |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Validation ran; no violations, or violations found without `--fail-on-error` |
| `1` | Violations found and `--fail-on-error` was passed |
| `2` | Bad config, unreadable input, or unwritable report |

## Rules configuration

```json
{
  "delimiter": ",",
  "allow_extra_columns": true,
  "columns": {
    "employee_id": { "type": "integer", "required": true, "unique": true, "min": 1 },
    "email":       { "type": "email", "required": true, "unique": true, "case_sensitive": false },
    "department":  { "type": "string", "required": true, "allowed_values": ["Engineering", "HR"] },
    "hire_date":   { "type": "date", "format": "%Y-%m-%d", "min": "2000-01-01" },
    "phone":       { "type": "string", "pattern": "^\\+?[0-9][0-9\\- ]{7,14}$" }
  }
}
```

File-level keys:

- `delimiter` — field separator, default `,`
- `allow_extra_columns` — when `false`, columns absent from the rules are reported

Per-column rules:

| Rule | Applies to | Meaning |
| --- | --- | --- |
| `type` | all | `string`, `integer`, `number`, `boolean`, `date`, `datetime`, `email` |
| `required` | all | Blank or missing value is a violation |
| `unique` | all | Duplicate values are reported with the row of first occurrence |
| `allowed_values` | all | Value must be in the list |
| `pattern` | all | Regular expression the value must match |
| `min_length` / `max_length` | all | Character-length bounds |
| `min` / `max` | numeric, date, datetime | Value bounds; dates use the column `format` |
| `format` | date, datetime | `strptime` format, default `%Y-%m-%d` / `%Y-%m-%d %H:%M:%S` |
| `case_sensitive` | string, email | When `false`, `allowed_values` and `unique` ignore case |

Columns declared in the rules but missing from the file are reported once as file-level
problems and skipped per row. Blank optional values are skipped rather than type-checked.

## Report contents

Every report carries the same data in three shapes:

- **text** — summary counters, file-level problems, violation counts per rule, then each invalid row with its failing columns
- **json** — full structure: `summary` (row counts, violations by rule and by column), `invalid_records` (row number, the original record, its violations), `file_level_violations`
- **csv** — one row per violation: `row_number, column, rule, message, value`

Row numbers are 1-based against the file including the header, so the first data row is `2`.

## Example

```
$ python3 validate_csv.py examples/employees.csv -c examples/rules.employees.json
Rows read       : 6
Valid rows      : 2
Invalid rows    : 4
Total violations: 11
...
  Row 6
    employee_id    unique       duplicate value, first seen on row 2 (value: '1')
    salary         min          value is below the minimum 20000 (value: '15000')
```
