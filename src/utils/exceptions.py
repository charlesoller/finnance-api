"""This module contains all custom exception used by the app"""


class NotFoundException(Exception):
    """Exception raised when a resource or path is not found."""

    def __init__(self, message: str):
        super().__init__(message)
