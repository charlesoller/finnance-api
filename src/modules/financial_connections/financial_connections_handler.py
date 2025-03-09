"""This module contains the handler for all Financial Connections functionality"""

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from src.utils import TransactionData, TransactionRange


class CustomerAuthRequest(BaseModel):
    """Request format for authorizing via Stripe"""

    email: EmailStr


class FinancialConnectionsHandler:
    """This class is responsible for handling financial connections requests"""

    def __init__(self, financial_connections_service):
        self.router = APIRouter(
            prefix="/financial-connections", tags=["financial-connections"]
        )
        self.__financial_connections_service = financial_connections_service
        self.__setup_routes()

    def __setup_routes(self):
        """Initializes all routes"""
        # Accounts routes
        self.router.get("/accounts/customer/{customer_id}")(
            self.get_accounts_by_customer
        )
        self.router.get("/accounts/email/{email}")(self.get_customer_by_email)
        self.router.get("/accounts/{account_id}")(self.get_account_by_id)
        self.router.get("/accounts/{account_id}/transactions")(self.get_transactions)
        self.router.post("/accounts")(self.handle_auth_flow)
        self.router.delete("/accounts/{account_id}")(self.disconnect_account)

        # Transactions routes
        # self.router.get("/transactions/customer/{customer_id}")(
        #     self.get_customer_transactions
        # )
        self.router.get("/transactions/{transaction_id}")(self.get_transaction)
        self.router.post("/transactions/data")(self.get_transaction_data)

    def __validate_customer_id(self, customer_id: str) -> bool:
        """Validates the customer ID format"""
        return bool(re.fullmatch(r"cus_[a-zA-Z0-9]{12,}", customer_id))

    def __validate_account_id(self, account_id: str) -> bool:
        """Validates the account ID format"""
        return bool(re.fullmatch(r"fca_[a-zA-Z0-9]{24}", account_id))

    async def get_accounts_by_customer(self, customer_id: str):
        """Get accounts for a specific customer"""
        if not self.__validate_customer_id(customer_id):
            raise HTTPException(status_code=400, detail="Invalid customer ID format")

        try:
            return self.__financial_connections_service.get_accounts(customer_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Customer not found: {customer_id}\n\nError: {e}",
            ) from e

    async def get_customer_by_email(self, email: EmailStr):
        """Get customer information by email"""

        try:
            return self.__financial_connections_service.get_customer_by_email(
                str(email)
            )
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Customer not found for email: {email}\n\nError: {e}",
            ) from e

    async def get_account_by_id(self, account_id: str):
        """Get account by ID"""
        if not self.__validate_account_id(account_id):
            raise HTTPException(status_code=400, detail="Invalid account ID format")

        try:
            return self.__financial_connections_service.get_account_by_id(account_id)
        except Exception as e:
            raise HTTPException(
                status_code=404, detail=f"Account not found: {account_id}\n\nError: {e}"
            ) from e

    async def get_transaction(self, transaction_id: str):
        """Gets a transaction by its ID"""
        try:
            return self.__financial_connections_service.get_transaction_by_id(
                transaction_id
            )
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction not found: {transaction_id}\n\nError: {e}",
            ) from e

    async def get_transactions(self, account_id: str):
        """Get transactions for a specific account"""
        if not self.__validate_account_id(account_id):
            raise HTTPException(status_code=400, detail="Invalid account ID format")

        try:
            return self.__financial_connections_service.get_transactions(account_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Transactions not found for account: {account_id}\n\nError: {e}",
            ) from e

    async def get_transaction_data(self, body: TransactionData):
        """Get transactions with range"""
        try:
            customer_id = body.get("customer_id", None)
            if not customer_id or not self.__validate_customer_id(customer_id):
                raise HTTPException(status_code=400, detail="Invalid account ID format")

            tx_range = body.get("range", TransactionRange.WEEK)

            return self.__financial_connections_service.get_transaction_data(
                customer_id=customer_id, tx_range=tx_range
            )
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Error retrieving transaction data\n\nError: {e}",
            ) from e

    async def handle_auth_flow(self, body: CustomerAuthRequest):
        """Handle customer authentication flow"""
        try:
            return self.__financial_connections_service.handle_auth_flow(body)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def disconnect_account(self, account_id: str):
        """Disconnect a specific account"""
        if not self.__validate_account_id(account_id):
            raise HTTPException(status_code=400, detail="Invalid account ID format")

        try:
            return self.__financial_connections_service.disconnect_account(account_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
