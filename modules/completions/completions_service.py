from utils import build_response
from datetime import datetime
import uuid
class CompletionsService:
  def __init__(self, logger, db, client):
    self.__logger = logger
    self.__db = db
    self.__client = client

  def get_all(self):
    return build_response(200, { 'Message': 'Success! Here are all of the completions...' })
  
  def create_generation(self, body):
    message_content = body['message_content']
    user_id = body['user_id']
    session_id = body['session_id']

    self.__save_message(user_id, session_id, "USER", message_content)

    completion = self.__generate(message_content)

    self.__save_message(user_id, session_id, "AI", completion)

    return build_response(200, { "body": completion })
  
  def __generate(self, message_content):
    try: 
      completion = self.__client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": message_content
            }
        ]
      )

      response = completion.choices[0].message.content
      self.__logger.info(f'Completion: {str(response)}')
    except Exception as e: 
      raise Exception(f'Failed to generate completion: {str(e)}')
    
    return response
  
  def __save_message(self, user_id, session_id, message_type, message_content):
    timestamp = datetime.now()
    item = {
        'id': str(uuid.uuid4()),
        'user_id': str(user_id),
        'session_id': str(session_id),
        'message_type': str(message_type),
        'message_content': str(message_content),
        'timestamp': str(timestamp)
    }
    self.__db.put_item(Item=item)
    return item