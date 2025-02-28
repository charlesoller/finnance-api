"""Server entry point. Also responsible for config."""

import logging
import os

import boto3
import stripe
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from src.modules import (
    FinancialConnectionsHandler,
    FinancialConnectionsService,
    SessionsHandler,
    SessionsService,
)

load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Keys
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")

# Clients
stripe.api_key = STRIPE_API_KEY

# Database
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
CUSTOMERS_TABLE_NAME = "customers"

chat_logs_db = dynamodb.Table(CHAT_LOGS_TABLE_NAME)
session_info_db = dynamodb.Table(SESSION_INFO_TABLE_NAME)
customers_db = dynamodb.Table(CUSTOMERS_TABLE_NAME)

# Services
financial_connections_service = FinancialConnectionsService(
    db=customers_db, stripe=stripe
)
sessions_service = SessionsService(
    chat_logs_db=chat_logs_db, session_info_db=session_info_db
)

# Handlers
sessions_handler = SessionsHandler(sessions_service)
financial_connections_handler = FinancialConnectionsHandler(
    financial_connections_service
)

# App Setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_handler.router)
app.include_router(financial_connections_handler.router)


# Test Route
@app.get("/")
async def root():
    """Test Hello World route"""
    return {"message": "Hello World"}

handler = Mangum(app)
