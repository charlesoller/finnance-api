import os
import boto3
import logging
import json
from modules import *
from router import Router
from openai import OpenAI
from utils import options_request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

dynamodb = boto3.resource('dynamodb')
dynamodbTableName = 'chat_logs'
db = dynamodb.Table(dynamodbTableName)

completions_service = CompletionsService(logger, db, openai)
completions_handler = CompletionsHandler(logger, completions_service)


sessions_service = SessionsService(logger, db)
sessions_handler = SessionsHandler(logger, sessions_service)

router = Router(logger, completions_handler, sessions_handler)

def lambda_handler(event, context):
  logger.info(event)
  httpMethod = event['httpMethod']
  path = event['path']
  body = get_body(event)

  if httpMethod == options_request:
    return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
          'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
      },
      'body': ''
    }
 
  return router.handle_request(httpMethod, path, body)

def get_body(event):
  body = None
  if 'body' in event and event['body']:
    try:
        body = json.loads(event['body'])
    except json.JSONDecodeError as e:
      logger.error(f"Error parsing request body: {e}")
      return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Invalid JSON in request body'})
      }
  return body