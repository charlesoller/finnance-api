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


DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

if os.getenv("ENV") == "local":
    logger.info(f"Connecting to local DynamoDB at: {DYNAMODB_ENDPOINT}")
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )
else:
    dynamodb = boto3.resource("dynamodb")  

CHAT_LOGS_TABLE_NAME = "chat_logs"
SESSION_INFO_TABLE_NAME = "session_info"

chat_logs_db = dynamodb.Table(CHAT_LOGS_TABLE_NAME)
session_info_db = dynamodb.Table(SESSION_INFO_TABLE_NAME)

completions_service = CompletionsService(chat_logs_db, openai)

sessions_service = SessionsService(
    logger, completions_service, chat_logs_db, session_info_db
)
sessions_handler = SessionsHandler(sessions_service)

router = Router(sessions_handler)

logger.info(f"DynamoDB Endpoint: {DYNAMODB_ENDPOINT}")
logger.info(f"Environment: {os.getenv('ENV')}")
logger.info(f"Tables available: {list(dynamodb.tables.all())}")

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
