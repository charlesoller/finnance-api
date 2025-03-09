"""Types for financial connections functionality"""

from enum import Enum
from typing import TypedDict


class TransactionRange(str, Enum):
    """The possible values for range in transaction data"""

    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


class TransactionData(TypedDict):
    """This class represents the shape of ChatMessage data"""

    customer_id: str
    range: TransactionRange
