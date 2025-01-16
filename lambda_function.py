"""
This module contains the AWS Lambda function handler for processing requests
and routing them to the appropriate services.
"""

import json
import logging
import os

import boto3
from openai import OpenAI

from src.modules import CompletionsService, SessionsHandler, SessionsService, Router
from src.utils import OPTIONS_REQUEST

logger = logging.getLogger()
logger.setLevel(logging.INFO)

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

dynamodb = boto3.resource("dynamodb")

CHAT_LOGS_DEV_TABLE_NAME = "chat_logs_dev"
SESSION_INFO_DEV_TABLE_NAME = "session_info_dev"

chat_logs_dev_db = dynamodb.Table(CHAT_LOGS_DEV_TABLE_NAME)
session_info_dev_db = dynamodb.Table(SESSION_INFO_DEV_TABLE_NAME)

completions_service = CompletionsService(chat_logs_dev_db, openai)

sessions_service = SessionsService(
    logger, completions_service, chat_logs_dev_db, session_info_dev_db
)
sessions_handler = SessionsHandler(sessions_service)

router = Router(sessions_handler)


def lambda_handler(event, context):
    """Handles incoming requests and routes them based on the HTTP method and path."""
    http_method = event["httpMethod"]
    path = event["path"]
    body = get_body(event)

    if http_method == OPTIONS_REQUEST:
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",  # noqa: E501
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            },
            "body": "",
        }

    return router.handle_request(http_method, path, body)


def get_body(event):
    """Extracts and parses the body from the incoming event."""
    body = None
    if "body" in event and event["body"]:
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError as e:
            logger.error("Error parsing request body: %s", e)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid JSON in request body"}),
            }
    return body
