"""
This module contains all logic needed for interacting with the Stripe Financial Connections API
"""

from datetime import datetime, timezone


class FinancialConnectionsService:
    """This class contains all logic for interacting with Stripe Financial Connections"""

    def __init__(self, db, stripe):
        self.__db = db
        self.__stripe = stripe

    def handle_auth_flow(self, body):
        """Handles the auth flow for integrating with Stripe"""
        customer_id = ""
        email = body.get("email", "")
        if not len(email) > 0:
            raise RuntimeError("No email found in body of request")

        existing_customer = self.get_customer_by_email(email)
        customer_id = existing_customer.get("customer_id")
        if not existing_customer:
            new_customer = self.__create_customer(email)
            customer_id = new_customer.get("customer_id")

        client_secret = self.__create_session(customer_id)
        return client_secret

    def __create_customer(self, email):
        """Creates a new Stripe customer and inserts data into DynamoDB"""
        new_customer = self.__stripe.Customer.create(email=email)

        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            "customer_id": new_customer.get("id"),
            "email": new_customer.get("email"),
            "timestamp": str(timestamp),
        }

        self.__db.put_item(Item=item)

        return item

    def __create_session(self, customer_id: str):
        """Creates the session for authorizing via Stripe"""
        res = self.__stripe.financial_connections.Session.create(
            account_holder={"type": "customer", "customer": str(customer_id)},
            permissions=["balances", "transactions"],
        )

        secret = res.get("client_secret", "")
        return secret

    def get_accounts(self, customer_id: str):
        """Gets all accounts for a user given their customer ID"""
        accounts = self.__stripe.financial_connections.Account.list(
            account_holder={"customer": str(customer_id)}
        )
        data = accounts.get("data", [])

        for account in data:
            if account.balance_refresh is None and account.status != "inactive":
                self.__subscribe_to_acct(account.id)
                self.__refresh_balance(account.id)

        return data

    def get_customer_by_email(self, email: str):
        """Gets a customer record from DDB from the user's email"""
        res = self.__db.get_item(Key={"email": email})

        item = res.get("Item", {})
        return item

    def __subscribe_to_acct(self, account_id: str):
        """Subscribes to transactions for an acct"""
        res = self.__stripe.financial_connections.Account.subscribe(
            str(account_id),
            features=["transactions"],
        )

        return res

    def __refresh_balance(self, account_id: str):
        """Refreshes the balance for an account"""
        res = self.__stripe.financial_connections.Account.refresh_account(
            account_id, features=["balance"]
        )
        print(f"The refresh val: {res}")
        return res
