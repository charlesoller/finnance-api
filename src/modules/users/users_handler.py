"""This module handles all requests to the /sessions endpoint"""

from fastapi import APIRouter, HTTPException


class UsersHandler:
    """This class is responsible for handling any requests to /users"""

    def __init__(self, users_service):
        self.router = APIRouter(prefix="/users", tags=["users"])
        self.__users_service = users_service
        self.__setup_routes()

    def __setup_routes(self):
        """Initializes all routes"""
        self.router.put("/{email}/omit/{account_id}")(self.omit_acct)
        self.router.get("/{email}/omitted-accounts")(self.get_omitted_accounts)

    async def omit_acct(self, email: str, account_id: str):
        """Handles omitting/unomitting an account"""
        try:
            return self.__users_service.omit_account(
                user_email=email,
                account_id=account_id,
            )
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_omitted_accounts(self, email: str):
        """Gets a users omitted accounts"""
        try:
            return self.__users_service.get_omitted_accounts(user_email=email)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
