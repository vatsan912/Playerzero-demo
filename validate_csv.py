#!/usr/bin/env python3
"""Validate a CSV file against configurable data-quality rules."""

import argparse
import csv
import json
import re
import sys
from datetime import datetime

VERSION = "1.0.0"

TYPE_NAMES = ("string", "integer", "number", "boolean", "date", "datetime", "email")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
BOOL_TRUE = {"true", "t", "yes", "y", "1"}
BOOL_FALSE = {"false", "f", "no", "n", "0"}


class ConfigError(Exception):
    pass


class Violation:
    def __init__(self, row_number, column, rule, message, value):
        self.row_number = row_number
        self.column = column
        self.rule = rule
        self.message = message
        self.value = value

    def as_dict(self):
        return {
            "row_number": self.row_number,
            "column": self.column,
            "rule": self.rule,
            "message": self.message,
            "value": self.value,
        }


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        try:
            config = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ConfigError("%s is not valid JSON: %s" % (path, exc))

    if not isinstance(config, dict):
        raise ConfigError("config root must be an object")

    columns = config.get("columns")
    if not isinstance(columns, dict) or not columns:
        raise ConfigError("config must define a non-empty 'columns' object")

    for name, spec in columns.items():
        if not isinstance(spec, dict):
            raise ConfigError("rules for column '%s' must be an object" % name)
        declared_type = spec.get("type", "string")
        if declared_type not in TYPE_NAMES:
            raise ConfigError(
                "column '%s' has unsupported type '%s' (supported: %s)"
                % (name, declared_type, ", ".join(TYPE_NAMES))
            )
        pattern = spec.get("pattern")
        if pattern is not None:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ConfigError("column '%s' has an invalid pattern: %s" % (name, exc))

    return config


def is_blank(value):
    return value is None or value.strip() == ""


def parse_typed_value(value, declared_type, spec):
    if declared_type == "integer":
        try:
            return int(value.strip()), None
        except ValueError:
            return None, "expected an integer"
    if declared_type == "number":
        try:
            return float(value.strip()), None
        except ValueError:
            return None, "expected a number"
    if declared_type == "boolean":
        lowered = value.strip().lower()
        if lowered in BOOL_TRUE:
            return True, None
        if lowered in BOOL_FALSE:
            return False, None
        return None, "expected a boolean"
    if declared_type in ("date", "datetime"):
        default_format = "%Y-%m-%d" if declared_type == "date" else "%Y-%m-%d %H:%M:%S"
        date_format = spec.get("format", default_format)
        try:
            return datetime.strptime(value.strip(), date_format), None
        except ValueError:
            return None, "expected %s matching format '%s'" % (declared_type, date_format)
    if declared_type == "email":
        if EMAIL_PATTERN.match(value.strip()):
            return value.strip(), None
        return None, "expected a valid email address"
    return value, None


def check_bounds(parsed, declared_type, spec, column, row_number, value, violations):
    minimum = spec.get("min")
    maximum = spec.get("max")
    if minimum is None and maximum is None:
        return

    if declared_type in ("integer", "number"):
        comparable = parsed
        low, high = minimum, maximum
    elif declared_type in ("date", "datetime"):
        default_format = "%Y-%m-%d" if declared_type == "date" else "%Y-%m-%d %H:%M:%S"
        date_format = spec.get("format", default_format)
        comparable = parsed
        low = datetime.strptime(minimum, date_format) if minimum is not None else None
        high = datetime.strptime(maximum, date_format) if maximum is not None else None
    else:
        return

    if low is not None and comparable < low:
        violations.append(
            Violation(row_number, column, "min", "value is below the minimum %s" % minimum, value)
        )
    if high is not None and comparable > high:
        violations.append(
            Violation(row_number, column, "max", "value is above the maximum %s" % maximum, value)
        )


def validate_cell(column, value, spec, row_number, violations):
    declared_type = spec.get("type", "string")

    if is_blank(value):
        if spec.get("required", False):
            violations.append(
                Violation(row_number, column, "required", "value is missing or blank", value)
            )
        return None

    stripped = value.strip()

    if declared_type != "string":
        parsed, error = parse_typed_value(value, declared_type, spec)
        if error is not None:
            violations.append(Violation(row_number, column, "type", error, value))
            return None
    else:
        parsed = stripped

    min_length = spec.get("min_length")
    max_length = spec.get("max_length")
    if min_length is not None and len(stripped) < min_length:
        violations.append(
            Violation(
                row_number,
                column,
                "min_length",
                "value is shorter than %s characters" % min_length,
                value,
            )
        )
    if max_length is not None and len(stripped) > max_length:
        violations.append(
            Violation(
                row_number,
                column,
                "max_length",
                "value is longer than %s characters" % max_length,
                value,
            )
        )

    allowed = spec.get("allowed_values")
    if allowed is not None:
        candidates = [str(item) for item in allowed]
        if spec.get("case_sensitive", True):
            matched = stripped in candidates
        else:
            matched = stripped.lower() in [item.lower() for item in candidates]
        if not matched:
            violations.append(
                Violation(
                    row_number,
                    column,
                    "allowed_values",
                    "value is not one of: %s" % ", ".join(candidates),
                    value,
                )
            )

    pattern = spec.get("pattern")
    if pattern is not None and not re.search(pattern, stripped):
        violations.append(
            Violation(row_number, column, "pattern", "value does not match pattern %s" % pattern, value)
        )

    check_bounds(parsed, declared_type, spec, column, row_number, value, violations)

    return stripped


def validate_header(header, config, violations):
    columns = config["columns"]
    header = header or []
    missing = [name for name in columns if name not in header]
    for name in missing:
        violations.append(
            Violation(0, name, "missing_column", "column declared in the rules is absent from the file", None)
        )

    if not config.get("allow_extra_columns", True):
        for name in header:
            if name not in columns:
                violations.append(
                    Violation(0, name, "unexpected_column", "column is not declared in the rules", None)
                )
    return missing


def validate_file(csv_path, config, delimiter=None, encoding="utf-8"):
    columns = config["columns"]
    delimiter = delimiter or config.get("delimiter", ",")
    unique_columns = [name for name, spec in columns.items() if spec.get("unique", False)]
    unique_seen = {name: {} for name in unique_columns}

    violations = []
    invalid_rows = {}
    total_rows = 0

    with open(csv_path, "r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        missing = set(validate_header(reader.fieldnames, config, violations))

        for offset, row in enumerate(reader):
            total_rows += 1
            row_number = offset + 2
            row_violations = []

            for column, spec in columns.items():
                if column in missing:
                    continue
                value = row.get(column)
                cleaned = validate_cell(column, value, spec, row_number, row_violations)

                if column in unique_seen and cleaned:
                    key = cleaned if spec.get("case_sensitive", True) else cleaned.lower()
                    first_seen = unique_seen[column].get(key)
                    if first_seen is None:
                        unique_seen[column][key] = row_number
                    else:
                        row_violations.append(
                            Violation(
                                row_number,
                                column,
                                "unique",
                                "duplicate value, first seen on row %s" % first_seen,
                                value,
                            )
                        )

            if row_violations:
                invalid_rows[row_number] = {
                    "row_number": row_number,
                    "record": row,
                    "violations": [item.as_dict() for item in row_violations],
                }
                violations.extend(row_violations)

    rule_counts = {}
    for item in violations:
        rule_counts[item.rule] = rule_counts.get(item.rule, 0) + 1

    column_counts = {}
    for item in violations:
        column_counts[item.column] = column_counts.get(item.column, 0) + 1

    return {
        "file": csv_path,
        "validator_version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total_rows": total_rows,
            "valid_rows": total_rows - len(invalid_rows),
            "invalid_rows": len(invalid_rows),
            "total_violations": len(violations),
            "violations_by_rule": rule_counts,
            "violations_by_column": column_counts,
        },
        "invalid_records": [invalid_rows[key] for key in sorted(invalid_rows)],
        "file_level_violations": [item.as_dict() for item in violations if item.row_number == 0],
    }


def render_text(report, max_records=None):
    summary = report["summary"]
    lines = []
    lines.append("Data-quality report for %s" % report["file"])
    lines.append("-" * 60)
    lines.append("Rows read       : %s" % summary["total_rows"])
    lines.append("Valid rows      : %s" % summary["valid_rows"])
    lines.append("Invalid rows    : %s" % summary["invalid_rows"])
    lines.append("Total violations: %s" % summary["total_violations"])

    if report["file_level_violations"]:
        lines.append("")
        lines.append("File-level problems:")
        for item in report["file_level_violations"]:
            lines.append("  [%s] %s: %s" % (item["rule"], item["column"], item["message"]))

    if summary["violations_by_rule"]:
        lines.append("")
        lines.append("Violations by rule:")
        for rule in sorted(summary["violations_by_rule"]):
            lines.append("  %-16s %s" % (rule, summary["violations_by_rule"][rule]))

    records = report["invalid_records"]
    if records:
        shown = records if max_records is None else records[:max_records]
        lines.append("")
        lines.append("Invalid records:")
        for record in shown:
            lines.append("  Row %s" % record["row_number"])
            for item in record["violations"]:
                lines.append(
                    "    %-14s %-12s %s (value: %r)"
                    % (item["column"], item["rule"], item["message"], item["value"])
                )
        if max_records is not None and len(records) > max_records:
            lines.append("  ... %s more invalid rows omitted" % (len(records) - max_records))

    return "\n".join(lines)


def render_csv_rows(report):
    rows = [("row_number", "column", "rule", "message", "value")]
    for item in report["file_level_violations"]:
        rows.append((item["row_number"], item["column"], item["rule"], item["message"], item["value"]))
    for record in report["invalid_records"]:
        for item in record["violations"]:
            rows.append(
                (item["row_number"], item["column"], item["rule"], item["message"], item["value"])
            )
    return rows


def write_report(report, destination, output_format, max_records):
    if output_format == "json":
        payload = json.dumps(report, indent=2, default=str)
        if destination is None:
            print(payload)
        else:
            with open(destination, "w", encoding="utf-8") as handle:
                handle.write(payload + "\n")
        return

    if output_format == "csv":
        rows = render_csv_rows(report)
        if destination is None:
            writer = csv.writer(sys.stdout)
            writer.writerows(rows)
        else:
            with open(destination, "w", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerows(rows)
        return

    payload = render_text(report, max_records)
    if destination is None:
        print(payload)
    else:
        with open(destination, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="validate_csv.py",
        description="Validate a CSV file against configurable data-quality rules and report invalid records.",
    )
    parser.add_argument("csv_file", help="path to the CSV file to validate")
    parser.add_argument("-c", "--config", required=True, help="path to the JSON rules configuration")
    parser.add_argument("-o", "--output", help="write the report to this path instead of stdout")
    parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        choices=("text", "json", "csv"),
        default="text",
        help="report format (default: text)",
    )
    parser.add_argument("-d", "--delimiter", help="CSV delimiter, overrides the config value")
    parser.add_argument("-e", "--encoding", default="utf-8", help="input file encoding (default: utf-8)")
    parser.add_argument(
        "--max-records",
        type=int,
        default=50,
        help="maximum invalid records listed in the text report, 0 for all (default: 50)",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="exit with status 1 when any violation is found",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, OSError) as exc:
        print("configuration error: %s" % exc, file=sys.stderr)
        return 2

    try:
        report = validate_file(args.csv_file, config, args.delimiter, args.encoding)
    except OSError as exc:
        print("could not read input: %s" % exc, file=sys.stderr)
        return 2
    except (ValueError, re.error) as exc:
        print("validation error: %s" % exc, file=sys.stderr)
        return 2

    max_records = None if args.max_records == 0 else args.max_records
    try:
        write_report(report, args.output, args.output_format, max_records)
    except OSError as exc:
        print("could not write report: %s" % exc, file=sys.stderr)
        return 2

    if args.fail_on_error and report["summary"]["total_violations"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
