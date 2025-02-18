"""This module contains the handler for all Financial Connections functionality"""

import re

from src.utils import (
    DELETE_REQUEST,
    FINANCIAL_CONNECTIONS_PATH,
    GET_REQUEST,
    POST_REQUEST,
    NotFoundException,
    build_response,
)


class FinancialConnectionsHandler:
    """This class is responsible for handling any requests to /sessions"""

    def __init__(self, financial_connections_service):
        self.__financial_connections_service = financial_connections_service

    def __extract_path(self, path: str):
        """This method extracts the base session path"""
        base = FINANCIAL_CONNECTIONS_PATH
        if path == base:
            return "/"
        if path.startswith(base):
            start = len(base)
            return path[start:]
        return path

    def __extract_customer_id(self, path: str):
        """This method gets the customer ID when the request is targeted to /accounts/:customerId"""

        match = re.fullmatch(r"/accounts/(cus_[a-zA-Z0-9]{12,})", path)
        if match:
            return match.group(1)
        return None

    def __extract_account_id(self, path: str):
        """
        This method gets the accountId when the request is targeted to
        /transactions|accounts/:transactionId
        """

        match = re.fullmatch(r"/(?:transactions|accounts)/(fca_[a-zA-Z0-9]{24})", path)
        if match:
            return match.group(1)
        return None

    def __extract_email(self, path: str):
        """This method gets the email when the request is targeted to /accounts/:email"""

        # Match an email pattern (simple regex for validation) in the path
        match = re.fullmatch(
            r"/accounts/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", path
        )

        if match:
            return match.group(1)
        return None

    def handle(self, method, path: str, body):
        """This method handles incoming requests directed to financial-connections"""
        subpath = self.__extract_path(path)
        customer_id = self.__extract_customer_id(subpath)
        account_id = self.__extract_account_id(subpath)
        email = self.__extract_email(subpath)
        print(f"The subpath: {subpath}")
        print(f"Acct ID: {account_id}")

        if method == GET_REQUEST:
            if subpath.startswith("/accounts"):
                if customer_id:
                    return build_response(
                        200,
                        self.__financial_connections_service.get_accounts(customer_id),
                    )
                if email:
                    return build_response(
                        200,
                        self.__financial_connections_service.get_customer_by_email(
                            email
                        ),
                    )
                if account_id:
                    return build_response(
                        200,
                        self.__financial_connections_service.get_account_by_id(
                            account_id
                        ),
                    )
            if subpath.startswith("/transactions"):
                if account_id:
                    return build_response(
                        200,
                        self.__financial_connections_service.get_transactions(
                            account_id
                        ),
                    )
        if method == POST_REQUEST:
            if subpath == "/customers":
                return build_response(
                    200, self.__financial_connections_service.handle_auth_flow(body)
                )
        if method == DELETE_REQUEST:
            if subpath.startswith("/accounts"):
                if account_id:
                    return build_response(
                        200,
                        self.__financial_connections_service.disconnect_account(
                            account_id
                        ),
                    )

        raise NotFoundException(
            f"No matching path found for method={method}, path={path}"
        )
