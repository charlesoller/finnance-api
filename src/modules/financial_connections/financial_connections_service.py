"""
This module contains all logic needed for interacting with the Stripe Financial Connections API
"""

from datetime import datetime, timedelta, timezone

from src.utils import TransactionRange


class FinancialConnectionsService:
    """This class contains all logic for interacting with Stripe Financial Connections"""

    def __init__(self, db, stripe):
        self.__db = db
        self.__stripe = stripe

    def handle_auth_flow(self, body):
        """Handles the auth flow for integrating with Stripe"""
        customer_id = ""
        email = body.email
        if not len(email) > 0:
            raise RuntimeError("No email found in body of request")

        existing_customer = self.get_customer_by_email(email)
        customer_id = existing_customer.get("customer_id")
        if not existing_customer:
            new_customer = self.__create_customer(email)
            customer_id = new_customer.get("customer_id")

        client_secret = self.__create_session(customer_id)
        return client_secret

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
            account_holder={"customer": str(customer_id)}, limit=100
        )

        data = [
            account
            for account in accounts.get("data", [])
            if account.status != "disconnected"
        ]

        for account in data:
            self.__update_account(account=account)

        return data

    def get_account_by_id(self, account_id: str):
        """Gets an account by its ID"""
        account = self.__stripe.financial_connections.Account.retrieve(account_id)

        return account

    def get_customer_by_email(self, email: str):
        """Gets a customer record from DDB from the user's email"""
        res = self.__db.get_item(Key={"email": email})

        item = res.get("Item", {})
        return item

    def get_transactions(
        self, account_id: str, tx_range: TransactionRange = TransactionRange.SIX_MONTH
    ):
        """Gets transactions for an account given its id"""
        filter_params = {}
        has_more = True
        all_transactions: list[dict] = []
        start_after_id = None

        now = datetime.now(timezone.utc)
        start_date = now

        if tx_range == TransactionRange.WEEK:
            start_date = now - timedelta(days=7)
        elif tx_range == TransactionRange.MONTH:
            start_date = now - timedelta(days=30)
        elif tx_range == TransactionRange.THREE_MONTH:
            start_date = now - timedelta(days=90)
        elif tx_range == TransactionRange.SIX_MONTH:
            start_date = now - timedelta(days=180)

        start_timestamp = int(start_date.timestamp())
        filter_params = {"transacted_at": {"gte": start_timestamp}}

        while has_more and len(all_transactions) < 5000:
            transactions = self.__stripe.financial_connections.Transaction.list(
                account=account_id,
                limit=100,
                starting_after=start_after_id,
                **filter_params,
            )

            data = transactions.get("data", [])
            has_more = transactions.get("has_more", False)

            if len(data) > 0 and has_more:
                start_after_id = data[-1]["id"]

            all_transactions.extend(data)

            if not has_more:
                break

        return all_transactions

    def get_transaction_by_id(self, txn_id: str):
        """Gets an transaction by its ID"""
        transaction = self.__stripe.financial_connections.Transaction.retrieve(txn_id)

        return transaction

    def get_transaction_data(self, customer_id: str, tx_range: TransactionRange):
        """Gets transaction data about an account"""
        accounts = self.get_accounts(customer_id=customer_id)

        all_transactions = []
        for account in accounts:
            try:
                account_transactions = self.get_transactions(
                    account_id=account.id, tx_range=tx_range
                )

                txn_with_inst = [
                    {
                        **txn,
                        "institution_name": account.get("institution_name", None),
                        "acct_display_name": account.get("display_name", None),
                        "acct_last4": account.get("last4", None),
                    }
                    for txn in account_transactions
                ]

                all_transactions.extend(txn_with_inst)
            except Exception as e:
                print(e)

        corrected_transactions = self.__clean_transaction_data(
            transactions=all_transactions, accounts=accounts
        )
        corrected_transactions.sort(
            key=lambda x: x.get("transacted_at", 0), reverse=True
        )

        return corrected_transactions

    def disconnect_account(self, account_id: str):
        """Disconnects the account with the given account ID from a users profile"""
        res = self.__stripe.financial_connections.Account.disconnect(account_id)

        data = res.get("data", {})
        return data

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

    def __subscribe_to_acct(self, account_id: str):
        """Subscribes to transactions for an acct"""
        res = self.__stripe.financial_connections.Account.subscribe(
            str(account_id),
            features=["transactions"],
        )

        return res

    def __refresh_account_balance(self, account_id: str):
        """Refreshes the balance for an account"""
        res = self.__stripe.financial_connections.Account.refresh_account(
            account_id, features=["balance"]
        )

        return res

    def __refresh_account_transactions(self, account_id: str):
        """Refreshes the transactions for an account"""
        res = self.__stripe.financial_connections.Account.refresh_account(
            account_id, features=["transactions"]
        )

        return res

    def __update_account(self, account):
        """Performs approriate update actions on an account"""
        if account.balance_refresh is None and account.status == "active":
            self.__subscribe_to_acct(account_id=account.id)
            self.__refresh_account_balance(account_id=account.id)
            self.__refresh_account_transactions(account_id=account.id)
        else:
            balance_refresh = account.get("balance_refresh", {})
            transaction_refresh = account.get("transaction_refresh", {})

            bal_timestamp = balance_refresh.get("next_refresh_available_at", None)
            tx_timestamp = transaction_refresh.get("next_refresh_available_at", None)
            current_time = datetime.now(timezone.utc)

            if bal_timestamp:
                next_bal_refresh = datetime.fromtimestamp(
                    bal_timestamp, tz=timezone.utc
                )
                if current_time >= next_bal_refresh:
                    self.__refresh_account_balance(account_id=account.id)
            if tx_timestamp:
                next_tx_refresh = datetime.fromtimestamp(tx_timestamp, tz=timezone.utc)
                if current_time >= next_tx_refresh:
                    self.__refresh_account_transactions(account_id=account.id)

    def __clean_transaction_data(self, transactions, accounts):
        """Cleans the transaction data to display properly to user"""
        corrected_txns = self.__handle_acct_edge_cases(
            accounts=accounts, transactions=transactions
        )
        cleaned_txns = self.__dedupe_pending_transactions(transactions=corrected_txns)
        return cleaned_txns

    def __handle_acct_edge_cases(self, accounts, transactions):
        """Handles all edge case account types and corrects them"""
        corrected_txns = self.__handle_wealthfront_edge_case(
            accounts=accounts, transactions=transactions
        )
        # Add more edge case handling here as needed
        return corrected_txns

    def __handle_wealthfront_edge_case(self, accounts, transactions):
        """Handles fixing Transaction data for Wealthfront Cash Accounts e2e"""
        wealthfront_cash_acct = next(
            filter(
                lambda acct: acct.get("institution_name") == "Wealthfront" and acct.get("category") == "cash",
                accounts,
            ),
            None,
        )
        if wealthfront_cash_acct:
            corrected_transactions = self.__build_wealthfront_history(
                transactions=transactions, wf_acct=wealthfront_cash_acct
            )
            return corrected_transactions
        return transactions

    def __build_wealthfront_history(self, transactions, wf_acct):
        """Builds wealthfront deposit history, as Wealthfront doesn't provide this"""
        wealthfront_deposits = [
            txn
            for txn in transactions
            if "Wealthfront EDI PYMNTS" in txn.get("description", "")
        ]
        modified_deposits = [
            {
                **txn,
                "account": wf_acct.get("id", None),
                "institution_name": wf_acct.get("institution_name", "Wealthfront"),
                "acct_display_name": wf_acct.get(
                    "display_name", "Individual Cash Account"
                ),
                "acct_last4": wf_acct.get("last4", None),
                "amount": abs(txn.get("amount", 0)),
                "description": "Wealthfront Cash Account Deposit",
            }
            for txn in wealthfront_deposits
        ]
        transactions.extend(modified_deposits)
        return transactions

    def __dedupe_pending_transactions(self, transactions):
        """Dedupes transactions that have both a pending and posted status"""
        # Group transactions by their transacted_at timestamp
        grouped_by_time = {}
        for txn in transactions:
            transacted_at = txn.get("transacted_at")
            if transacted_at not in grouped_by_time:
                grouped_by_time[transacted_at] = []
            grouped_by_time[transacted_at].append(txn)

        # For each group, keep posted transactions and remove pending ones if both exist
        deduped_transactions = []
        for time_group in grouped_by_time.values():
            if len(time_group) > 1:
                # Check if we have both posted and pending transactions
                has_posted = any(txn.get("status") == "posted" for txn in time_group)
                if has_posted:
                    # Keep only posted transactions
                    deduped_transactions.extend(
                        [txn for txn in time_group if txn.get("status") == "posted"]
                    )
                else:
                    # If no posted transactions, keep all
                    deduped_transactions.extend(time_group)
            else:
                # Only one transaction at this time, keep it
                deduped_transactions.extend(time_group)

        return deduped_transactions
