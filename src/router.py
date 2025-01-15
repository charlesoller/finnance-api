"""
This module defines the Router class for handling HTTP requests.
"""

from src.utils.paths import SESSIONS_PATH


class Router:
    """Router class for handling HTTP requests."""

    def __init__(self, sessions_handler):
        self.__sessions_handler = sessions_handler

    def handle_request(self, method: str, path: str, body):
        """Handles incoming requests based on the HTTP method and path."""
        if path.startswith(SESSIONS_PATH):
            return self.__sessions_handler.handle(method, path, body)
        return None
