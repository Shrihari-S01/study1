"""
Currency Utilities.

Utility functions for handling
Indian currency values.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


class CurrencyUtils:
    """
    Utility class for currency operations.
    """

    CURRENCY_SYMBOLS = [
        "₹",
        "Rs.",
        "Rs",
        "INR",
    ]

    @staticmethod
    def clean(value: str) -> str:
        """
        Remove currency symbols and commas.
        """

        if not value:

            return ""

        value = value.strip()

        for symbol in CurrencyUtils.CURRENCY_SYMBOLS:

            value = value.replace(
                symbol,
                "",
            )

        value = value.replace(
            ",",
            "",
        )

        return value.strip()

    @staticmethod
    def is_valid(value: str) -> bool:
        """
        Validate currency value.
        """

        value = CurrencyUtils.clean(
            value,
        )

        if not value:

            return False

        try:

            Decimal(value)

            return True

        except InvalidOperation:

            return False

    @staticmethod
    def to_decimal(value: str) -> Decimal:
        """
        Convert currency string to Decimal.
        """

        value = CurrencyUtils.clean(
            value,
        )

        if not value:

            return Decimal("0")

        try:

            return Decimal(value)

        except InvalidOperation:

            return Decimal("0")

    @staticmethod
    def to_float(value: str) -> float:
        """
        Convert currency string to float.
        """

        return float(

            CurrencyUtils.to_decimal(
                value,
            )

        )

    @staticmethod
    def format_indian(value) -> str:
        """
        Format value with Indian commas.

        Example:
        1250000 -> ₹12,50,000.00
        """

        try:

            amount = float(value)

        except (TypeError, ValueError):

            amount = 0.0

        integer, decimal = f"{amount:.2f}".split(".")

        if len(integer) > 3:

            last_three = integer[-3:]

            remaining = integer[:-3]

            groups = []

            while len(remaining) > 2:

                groups.insert(

                    0,

                    remaining[-2:],

                )

                remaining = remaining[:-2]

            if remaining:

                groups.insert(

                    0,

                    remaining,

                )

            integer = ",".join(

                groups + [last_three]

            )

        return f"₹{integer}.{decimal}"

    @staticmethod
    def format_plain(value) -> str:
        """
        Return value without currency symbol.
        """

        try:

            amount = float(value)

        except (TypeError, ValueError):

            amount = 0.0

        return f"{amount:.2f}"

    @staticmethod
    def greater_than(
        first: str,
        second: str,
    ) -> bool:
        """
        Compare currency values.
        """

        return (

            CurrencyUtils.to_decimal(first)

            >

            CurrencyUtils.to_decimal(second)

        )

    @staticmethod
    def less_than(
        first: str,
        second: str,
    ) -> bool:
        """
        Compare currency values.
        """

        return (

            CurrencyUtils.to_decimal(first)

            <

            CurrencyUtils.to_decimal(second)

        )

    @staticmethod
    def equal(
        first: str,
        second: str,
    ) -> bool:
        """
        Check equality.
        """

        return (

            CurrencyUtils.to_decimal(first)

            ==

            CurrencyUtils.to_decimal(second)

        )

    @staticmethod
    def extract(text: str) -> str:
        """
        Extract first currency value
        from text.
        """

        if not text:

            return ""

        match = re.search(

            r"[\d,]+(?:\.\d{1,2})?",

            text,

        )

        if not match:

            return ""

        return match.group()

    @staticmethod
    def health_check() -> dict:
        """
        Utility status.
        """

        return {

            "service": "Currency Utils",

            "status": "Healthy",

            "currency": "INR",

            "symbols": CurrencyUtils.CURRENCY_SYMBOLS,

        }