"""This module contains all GET functionality needed for sessions"""


class UsersService:
    """This class contains all functionality relevant to sessions"""

    def __init__(self, db):
        self.__db = db

    def omit_account(self, user_email: str, account_id: str):
        """Handles omitting/unomitting accounts based on account id

        If the account_id is already in the omitted_accounts list, it will be removed.
        If it's not in the list, it will be added.

        Args:
            user_email (str): The email of the user to update
            account_id (str): The ID of the account to toggle omission status

        Returns:
            bool: True if the account was omitted, False if it was unomitted
        """
        response = self.__db.get_item(Key={"email": user_email})
        user_data = response.get("Item", {})

        if not user_data:
            self.__create_user(user_email)
            self.__db.update_item(
                Key={"email": user_email},
                UpdateExpression="SET omitted_accounts = :val",
                ExpressionAttributeValues={":val": [account_id]},
            )
            return True

        if "omitted_accounts" not in user_data or not user_data["omitted_accounts"]:
            self.__db.update_item(
                Key={"email": user_email},
                UpdateExpression="SET omitted_accounts = :val",
                ExpressionAttributeValues={":val": [account_id]},
            )
            return True

        omitted_accounts = user_data["omitted_accounts"]

        if account_id in omitted_accounts:
            omitted_accounts.remove(account_id)
            was_omitted = False
        else:
            omitted_accounts.append(account_id)
            was_omitted = True

        self.__db.update_item(
            Key={"email": user_email},
            UpdateExpression="SET omitted_accounts = :val",
            ExpressionAttributeValues={":val": omitted_accounts},
        )

        return was_omitted

    def get_omitted_accounts(self, user_email: str):
        """Retrieves the list of omitted accounts for a user

        Args:
            user_email (str): The email of the user

        Returns:
            list: List of omitted account IDs
        """
        response = self.__db.get_item(Key={"email": user_email})
        user_data = response.get("Item", {})

        if "omitted_accounts" not in user_data:
            return []

        return user_data["omitted_accounts"]

    def __create_user(self, user_email: str):
        self.__db.put_item(
            Item={
                "email": user_email,
            }
        )
