"""
Date Utilities.

Utility functions for handling
auction notice dates.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

SUPPORTED_DATE_FORMATS = [

    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",

    "%d/%m/%y",
    "%d-%m-%y",
    "%d.%m.%y",

    "%Y-%m-%d",

]

class DateUtils:
    """
    Utility class for date operations.
    """

    @staticmethod
    def parse(
        value: str,
    ) -> Optional[datetime]:
        """
        Convert string to datetime.
        """

        if not value:

            return None

        value = value.strip()

        for fmt in SUPPORTED_DATE_FORMATS:

            try:

                return datetime.strptime(
                    value,
                    fmt,
                )

            except ValueError:

                continue

        return None

    @staticmethod
    def format_iso(
        value: str,
    ) -> str:
        """
        Convert date into YYYY-MM-DD.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return ""

        return parsed.strftime(
            "%Y-%m-%d",
        )

    @staticmethod
    def format_indian(
        value: str,
    ) -> str:
        """
        Convert date into DD/MM/YYYY.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return ""

        return parsed.strftime(
            "%d/%m/%Y",
        )

    @staticmethod
    def is_valid(
        value: str,
    ) -> bool:
        """
        Validate date.
        """

        return DateUtils.parse(
            value,
        ) is not None

    @staticmethod
    def today() -> str:
        """
        Return today's date.
        """

        return datetime.today().strftime(
            "%Y-%m-%d",
        )

    @staticmethod
    def current_datetime() -> str:
        """
        Return current date and time.
        """

        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S",
        )

    @staticmethod
    def compare(
        first: str,
        second: str,
    ) -> int:
        """
        Compare two dates.

        Returns
        -------
        -1 : first < second
         0 : equal
         1 : first > second
        """

        d1 = DateUtils.parse(first)
        d2 = DateUtils.parse(second)

        if d1 is None or d2 is None:

            return 0

        if d1 < d2:

            return -1

        if d1 > d2:

            return 1

        return 0

    @staticmethod
    def days_between(
        start: str,
        end: str,
    ) -> int:
        """
        Calculate number of days.
        """

        start_date = DateUtils.parse(
            start,
        )

        end_date = DateUtils.parse(
            end,
        )

        if start_date is None or end_date is None:

            return 0

        return abs(

            (end_date - start_date).days

        )

    @staticmethod
    def is_future(
        value: str,
    ) -> bool:
        """
        Check whether date is in future.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return False

        return parsed.date() > date.today()

    @staticmethod
    def is_past(
        value: str,
    ) -> bool:
        """
        Check whether date is in past.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return False

        return parsed.date() < date.today()

    @staticmethod
    def year(
        value: str,
    ) -> int:
        """
        Return year.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return 0

        return parsed.year

    @staticmethod
    def month(
        value: str,
    ) -> int:
        """
        Return month.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return 0

        return parsed.month

    @staticmethod
    def day(
        value: str,
    ) -> int:
        """
        Return day.
        """

        parsed = DateUtils.parse(
            value,
        )

        if parsed is None:

            return 0

        return parsed.day

    @staticmethod
    def health_check() -> dict:
        """
        Utility status.
        """

        return {

            "service": "Date Utils",

            "status": "Healthy",

            "supported_formats": len(
                SUPPORTED_DATE_FORMATS,
            ),

        }