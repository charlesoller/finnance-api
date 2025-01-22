"""This module contains all functionality needed for sessions"""

import json
from datetime import datetime
from typing import List

from boto3.dynamodb.conditions import Key

from src.utils import SUMMARY_PROMPT, ChatMessage, GenerationRequest, build_response


class SessionsService:
    """This class contains all functionality relevant to sessions"""

    def __init__(self, logger, completions_service, chat_logs_db, session_info_db):
        self.__logger = logger
        self.__completions_service = completions_service
        self.__chat_logs_db = chat_logs_db
        self.__session_info_db = session_info_db

    def get_all_sessions_info(self):
        """This method returns all session info"""
        try:
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

            return build_response(200, sessions_info)
        except Exception as e:
            self.__logger.error(f"Error retrieving session info: {str(e)}")
            return build_response(500, {"message": "Internal server error"})

    def get_session(self, session_id: str):
        """This method gets detailed data on a session"""
        response = self.__chat_logs_db.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ExpressionAttributeNames={"#timestamp": "timestamp"},
            ProjectionExpression="""
            id, session_id, message_content, message_type, graph_data, #timestamp
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

            return build_response(200, sorted_items)

        return build_response(404, {"message": f"Session {session_id} not found"})

    def create_message_for_session(self, session_id: str, body: GenerationRequest):
        """Thid method creates a new chat within a session"""
        history = body.get("history", [])
        is_first_message = len(history) == 0

        new_messages = self.__completions_service.create_generation(session_id, body)
        updated_history = history + new_messages

        self.__update_session(session_id, updated_history, is_first_message)

        return build_response(200, {"body": new_messages})

    def __update_session(
        self, session_id: str, history: List[ChatMessage], is_first_message: bool
    ):
        """This method is responsible for updating session info"""
        if is_first_message:
            return self.__create_new_session(session_id, history)

        timestamp = datetime.now().isoformat()
        item_count = len(history)
        updating_name = False
        session_name = ""

        curr_session = self.__session_info_db.get_item(
            Key={"session_id": session_id},
            ProjectionExpression="last_updated_count, session_name",
        )

        item = curr_session.get("Item", {})
        last_updated_count = item.get("last_updated_count", 0)

        if 8 > last_updated_count <= item_count:
            # Update the title after 8 messages
            # Can Add additional logic here on how to determine when to update session name
            session_name = self.__generate_session_name(history)
            updating_name = True

        update_args = {
            ":updated_at": timestamp,
            ":item_count": item_count,
            ":last_updated_count": item_count if updating_name else last_updated_count,
        }

        update_expression = """
        SET updated_at = :updated_at, item_count = :item_count,
        last_updated_count = :last_updated_count
        """

        if updating_name:
            update_expression += ", session_name = :session_name"
            update_args[":session_name"] = session_name

        try:
            updated_item = self.__session_info_db.update_item(
                Key={"session_id": str(session_id)},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=update_args,
            )
            return updated_item
        except Exception as e:
            raise RuntimeError(f"Failed to update session: {e}") from e

    def __create_new_session(self, session_id: str, history: List[ChatMessage]):
        timestamp = datetime.now()
        session_name = self.__generate_session_name(history)

        item = {
            "session_id": str(session_id),
            "session_name": str(session_name),
            "created_at": str(timestamp),
            "updated_at": str(timestamp),
            "last_updated_count": len(history),
            "item_count": len(history),
        }

        self.__session_info_db.put_item(Item=item)

    def __generate_session_name(self, history):
        completion = self.__completions_service.generate(
            "Please generate a title for this conversation using your developer prompt.",
            history,
            SUMMARY_PROMPT,
        )

        json_completion = json.loads(completion)
        name = str(json_completion["title"])

        return name
