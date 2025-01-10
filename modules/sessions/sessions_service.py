from utils import build_response

class SessionsService:
  def __init__(self, logger, db):
    self.__logger = logger
    self.__db = db

  def get_all_session_ids(self):
      try:
          response = self.__db.scan(
              ProjectionExpression='session_id'  # Only retrieve the session_id attribute
          )
          
          session_ids = {item['session_id'] for item in response.get('Items', [])}  
          
          return build_response(200, list(session_ids))
      except Exception as e:
          self.__logger.error(f'Error retrieving session IDs: {str(e)}')
          return build_response(500, {'message': 'Internal server error'})


  def get_by_id(self, session_id):
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

    if 'Items' in response:
      sorted_items = sorted(response['Items'], key=lambda x: x['timestamp'])
      return build_response(200, sorted_items)
    else:
      return build_response(404, {'message': f'Session {session_id} not found'})
