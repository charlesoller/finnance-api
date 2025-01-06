import os
import boto3
import logging
from modules import *
from router import Router
from openai import OpenAI

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

dynamodb = boto3.resource('dynamodb')
dynamodbTableName = 'chat_logs'
db = dynamodb.Table(dynamodbTableName)

completions_service = CompletionsService(logger, db, client)
completions_handler = CompletionsHandler(logger, completions_service)

router = Router(logger, completions_handler)

def lambda_handler(event, context):
  logger.info(event)
  httpMethod = event['httpMethod']
  path = event['path']
  body = get_body(event)
 
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