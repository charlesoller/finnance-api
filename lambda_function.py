"""Lambda function entry point"""
from src.main import handler

def lambda_handler(event, context):
    """Lambda handler function that delegates to Mangum handler"""
    return handler(event, context)