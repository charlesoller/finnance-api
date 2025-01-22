"""This module handles all requests to the /sessions endpoint"""

import re

from src.utils import (
    GET_REQUEST,
    POST_REQUEST,
    SESSIONS_PATH,
    GenerationRequest,
    NotFoundException,
)


class SessionsHandler:
    """This class is responsible for handling any requests to /sessions"""

    def __init__(self, sessions_service):
        self.__sessions_service = sessions_service

    def __extract_path(self, path: str):
        """This method extracts the base session path"""
        base = SESSIONS_PATH
        if path == base:
            return "/"
        if path.startswith(base):
            start = len(base)
            return path[start:]
        return path

    def __extract_session_id(self, path: str):
        """This method gets the session ID when the request is targeted to /sessions/:sessionId"""

        if re.fullmatch(r"[a-f0-9\-]{36}", path[1:]):
            return path[1:]
        return None

    def handle(self, method, path: str, body: GenerationRequest):
        """This method handles all incoming requests to the SessionsHandler"""
        subpath = self.__extract_path(path)
        session_id = self.__extract_session_id(subpath)

        if method == GET_REQUEST:
            if subpath == "/":
                return self.__sessions_service.get_all_sessions_info()
            if session_id:
                return self.__sessions_service.get_session(session_id)

        elif method == POST_REQUEST:
            if session_id:
                return self.__sessions_service.create_message_for_session(
                    session_id, body
                )

        raise NotFoundException(
            f"No matching path found for method={method}, path={path}"
        )
