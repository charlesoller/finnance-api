"""This module handles all requests to the /sessions endpoint"""

import re

from fastapi import APIRouter, HTTPException


class SessionsHandler:
    """This class is responsible for handling any requests to /sessions"""

    def __init__(self, sessions_service):
        self.router = APIRouter(prefix="/sessions", tags=["sessions"])
        self.__sessions_service = sessions_service
        self.__setup_routes()

    def __setup_routes(self):
        """Initializes all routes"""
        self.router.get("")(self.get_all_sessions)
        self.router.get("/{session_id}")(self.get_session)

    async def get_all_sessions(self):
        """Get information for all sessions"""
        try:
            return self.__sessions_service.get_all_sessions_info()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_session(self, session_id: str):
        """Get information for a specific session"""
        if not self.__validate_session_id(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        try:
            return self.__sessions_service.get_session(session_id)
        except Exception as e:
            raise HTTPException(
                status_code=404, detail=f"Session not found: {session_id}\n\nError: {e}"
            ) from e

    def __validate_session_id(self, session_id: str) -> bool:
        """Validates the session ID format"""

        return bool(re.fullmatch(r"[a-f0-9\-]{36}", session_id))
