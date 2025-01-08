from utils import build_response

class SessionsService:
  def __init__(self, logger, db):
    self.__logger = logger
    self.__db = db

  def get_by_id(self, session_id):
    print(f'The session ID: {session_id}')
    response = self.__db.scan(
        FilterExpression='session_id = :sid',
        ExpressionAttributeValues={
            ':sid': session_id
        },
        ExpressionAttributeNames={
          '#timestamp': 'timestamp'
        },
        ProjectionExpression='id, session_id, message_content, message_type, #timestamp'
    )

    print(f'The response: {response}')
    if 'Items' in response:
      sorted_items = sorted(response['Items'], key=lambda x: x['timestamp'])
      return build_response(200, sorted_items)
    else:
      return build_response(404, {'message': f'Session {session_id} not found'})
