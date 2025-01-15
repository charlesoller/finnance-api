"""This module contains all of the complex types needed in the sessions module"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ChartType(str, Enum):
    """This class contains an enum for the different types of chart"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"


class MessageOwner(str, Enum):
    """This class contains an enum for valid message owners"""

    USER = ("user",)
    AI = "ai"


@dataclass
class ChartDataPoint:
    """
    This class represents the shape of the data for a datapoint as returned by a
    ChatGPT completion
    """

    label: str
    amount: float


@dataclass
class GraphResponse:
    """This class represents the expected JSON response shape for a graph"""

    type: ChartType
    data: List[ChartDataPoint]


@dataclass
class ChatMessage:
    """This class represents the shape of ChatMessage data"""

    message_id: str
    user_id: str
    message_content: str
    message_type: MessageOwner
    session_id: str
    timestamp: str
    graph_data: Optional[GraphResponse] = None


@dataclass
class GenerationRequest:
    """This class represents the expected format of a generation request"""

    user_id: str
    session_id: str
    message_content: str
    history: List[ChatMessage]
    use_graph: bool
