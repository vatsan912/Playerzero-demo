import json
import re
import sys
from typing import Any


class CustomerValidator:
    REQUIRED_FIELDS = {
        "name",
        "email",
        "age",
        "phone",
        "active",
    }

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    PHONE_PATTERN = re.compile(r"^\d{10}$")

    def __init__(self, data: Any):
        self.data = data
        self.results = []

    def validate(self) -> list[dict]:
        """
        Validate all customer records.

        Returns a list containing the validation result
        for every customer.
        """

        if not isinstance(self.data, list):
            raise ValueError(
                "JSON root must be a list of customer objects."
            )

        for index, customer in enumerate(self.data, start=1):
            result = self.validate_customer(customer, index)
            self.results.append(result)

        return self.results

    def validate_customer(
        self,
        customer: Any,
        customer_number: int,
    ) -> dict:
        """
        Validate a single customer record.
        """

        errors = []

        # --------------------------------------------------
        # Check that customer is an object
        # --------------------------------------------------

        if not isinstance(customer, dict):
            return {
                "customer": customer_number,
                "valid": False,
                "errors": [
                    "Customer entry must be a JSON object."
                ],
            }

        # --------------------------------------------------
        # Check required fields
        # --------------------------------------------------

        missing_fields = (
            self.REQUIRED_FIELDS - customer.keys()
        )

        for field in sorted(missing_fields):
            errors.append(
                f"Missing required field: '{field}'."
            )

        # --------------------------------------------------
        # Name validation
        # --------------------------------------------------

        if "name" in customer:
            name = customer["name"]

            if not isinstance(name, str):
                errors.append(
                    "Name must be a string."
                )

            elif not name.strip():
                errors.append(
                    "Name cannot be empty."
                )

        # --------------------------------------------------
        # Email validation
        # --------------------------------------------------

        if "email" in customer:
            email = customer["email"]

            if not isinstance(email, str):
                errors.append(
                    "Email must be a string."
                )

            elif not self.EMAIL_PATTERN.match(
                email.strip()
            ):
                errors.append(
                    f"Invalid email format: '{email}'."
                )

        # --------------------------------------------------
        # Age validation
        # --------------------------------------------------

        if "age" in customer:
            age = customer["age"]

            # bool is technically a subclass of int in Python,
            # so explicitly reject it.
            if isinstance(age, bool):
                errors.append(
                    "Age must be an integer."
                )

            elif not isinstance(age, int):
                errors.append(
                    f"Age must be an integer, got "
                    f"{type(age).__name__}."
                )

            elif age < 0 or age > 120:
                errors.append(
                    f"Age must be between 0 and 120, got {age}."
                )

        # --------------------------------------------------
        # Phone validation
        # --------------------------------------------------

        if "phone" in customer:
            phone = customer["phone"]

            # Phone numbers should ideally be stored as strings
            # so leading zeroes are not lost.
            if not isinstance(phone, str):
                errors.append(
                    "Phone must be a string containing exactly "
                    "10 digits."
                )

            elif not self.PHONE_PATTERN.fullmatch(
                phone.strip()
            ):
                errors.append(
                    f"Phone must contain exactly 10 digits: "
                    f"'{phone}'."
                )

        # --------------------------------------------------
        # Active validation
        # --------------------------------------------------

        if "active" in customer:
            active = customer["active"]

            if not isinstance(active, str):
                errors.append(
                    "Active must be either 'yes' or 'no'."
                )

            elif active.strip().lower() not in {
                "yes",
                "no",
            }:
                errors.append(
                    f"Active must be either 'yes' or 'no', "
                    f"got '{active}'."
                )

        # --------------------------------------------------
        # Return result
        # --------------------------------------------------

        return {
            "customer": customer_number,
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def get_summary(self) -> dict:
        """
        Return summary statistics after validation.
        """

        total = len(self.results)

        valid = sum(
            result["valid"]
            for result in self.results
        )

        invalid = total - valid

        return {
            "total_customers": total,
            "valid_customers": valid,
            "invalid_customers": invalid,
        }

    def print_report(self) -> None:
        """
        Print a human-readable validation report.
        """

        print("\n" + "=" * 60)
        print("             CUSTOMER VALIDATION REPORT")
        print("=" * 60)

        for result in self.results:
            customer_number = result["customer"]

            if result["valid"]:
                print(
                    f"\nCustomer {customer_number}: VALID"
                )

            else:
                print(
                    f"\nCustomer {customer_number}: INVALID"
                )

                for error in result["errors"]:
                    print(f"  - {error}")

        summary = self.get_summary()

        print("\n" + "-" * 60)
        print("SUMMARY")
        print("-" * 60)

        print(
            f"Total customers   : "
            f"{summary['total_customers']}"
        )

        print(
            f"Valid customers   : "
            f"{summary['valid_customers']}"
        )

        print(
            f"Invalid customers : "
            f"{summary['invalid_customers']}"
        )

        print("=" * 60)


def load_json_file(file_path: str) -> Any:
    """
    Load JSON data from a file.
    """

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except FileNotFoundError:
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON: {error}"
        )


def main() -> None:

    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "  python customer_validator.py customers.json"
        )

        sys.exit(1)

    file_path = sys.argv[1]

    try:
        data = load_json_file(file_path)

        validator = CustomerValidator(data)

        validator.validate()

        validator.print_report()

    except (
        FileNotFoundError,
        ValueError,
    ) as error:

        print(f"\nERROR: {error}")

        sys.exit(1)


if __name__ == "__main__":
    main()