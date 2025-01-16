"""This module contains all completions related functionality"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils import DEV_PROMPT
from src.utils.types import ChatMessage, GenerationRequest, GraphResponse, MessageOwner


class CompletionsService:
    """This class contains all completion related functionality with OpenAI"""

    def __init__(self, db, openai):
        self.__db = db
        self.__openai = openai

    def create_generation(self, session_id: str, body: GenerationRequest):
        """This method handles the entire generation flow"""
        message_content = body["message_content"]
        user_id = body["user_id"]
        history = body["history"]

        user_message = self.__save_message(
            user_id, session_id, MessageOwner.USER, message_content, graph_data=None
        )

        completion = self.generate(message_content, history)
        if completion:
            dict_completion = json.loads(completion)
        else:
            raise ValueError("Received an empty response from the completion API.")

        message = dict_completion["message"]
        graph = dict_completion.get("graph", None)

        ai_message = self.__save_message(
            user_id, session_id, MessageOwner.AI, message, graph
        )

        return [user_message, ai_message]

    def generate(
        self,
        message_content: str,
        history: List[ChatMessage],
        prompt: str = DEV_PROMPT,
        json_mode: bool = True,
    ):
        """This method is responsible for the generation of a completion"""
        print(f"TEST: {history}")
        try:
            params: Dict[str, Any] = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "developer", "content": prompt},
                    *self.__format_history(history),
                    {"role": "user", "content": message_content},
                ],
            }

            if json_mode:
                params["response_format"] = {"type": "json_object"}

            completion = self.__openai.chat.completions.create(**params)

            response = completion.choices[0].message.content
            return response
        except Exception as e:
            raise Exception(f"Failed to generate completion: {str(e)}") from e

    def __format_history(self, history: List[ChatMessage]):
        formatted = []
        for message in history:
            role: str = message["message_type"].lower()
            if role == "ai":
                role = "assistant"
            formatted.append({"role": role, "content": message["message_content"]})
        return formatted

    def __save_message(
        self,
        user_id: str,
        session_id: str,
        message_type: MessageOwner,
        message_content: str,
        graph_data: Optional[GraphResponse] = None,
    ):
        """This method is responsible for saving chats to the database"""
        timestamp = datetime.now().isoformat()
        item = {
            "message_id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "session_id": str(session_id),
            "message_type": str(message_type.value),
            "message_content": str(message_content),
            "timestamp": str(timestamp),
        }

        if graph_data:
            item["graph_data"] = json.dumps(graph_data)

        self.__db.put_item(Item=item)
        return item
