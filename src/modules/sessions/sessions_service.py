"""This module contains all GET functionality needed for sessions"""

import json

from boto3.dynamodb.conditions import Key


class SessionsService:
    """This class contains all functionality relevant to sessions"""

    def __init__(self, chat_logs_db, session_info_db):
        self.__chat_logs_db = chat_logs_db
        self.__session_info_db = session_info_db

    def get_all_sessions_info(self):
        """This method returns all session info"""
        response = self.__session_info_db.scan(
            ProjectionExpression="session_id, session_name, updated_at"
        )

        sessions_info = response.get("Items", [])
        sessions_info = [
            {
                "session_id": item["session_id"],
                "session_name": item["session_name"],
                "updated_at": item["updated_at"],
            }
            for item in sessions_info
        ]

        return sessions_info

    def get_session(self, session_id: str):
        """This method gets detailed data on a session"""
        response = self.__chat_logs_db.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ExpressionAttributeNames={"#timestamp": "timestamp"},
            ProjectionExpression="""
            id, session_id, thread_id, message_content, message_type, graph_data, #timestamp
            """,
        )

        if "Items" in response:
            sorted_items = sorted(response["Items"], key=lambda x: x["timestamp"])

            for item in sorted_items:
                if "graph_data" in item and item["graph_data"]:
                    try:
                        item["graph_data"] = json.loads(item["graph_data"])
                    except json.JSONDecodeError:
                        item["graph_data"] = None

            return sorted_items
        return []
