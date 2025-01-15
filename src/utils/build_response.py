"""
This module provides utilities for building JSON responses,
including a custom JSON encoder for Decimal objects.
"""

import json
from decimal import Decimal


class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling Decimal objects."""

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return json.JSONEncoder.default(self, o)


def build_response(status_code, body=None):
    """Builds a JSON response with the given status code and body."""
    response = {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    }
    if body is not None:
        response["body"] = json.dumps(body, cls=CustomEncoder)
    return response
