from utils import build_response
from datetime import datetime
import uuid
class CompletionsService:
  def __init__(self, logger, db, openai):
    self.__logger = logger
    self.__db = db
    self.__openai = openai

  def get_all(self):
    return build_response(200, { 'Message': 'Success! Here are all of the completions...' })
  
  def create_generation(self, body):
    print(f'Body: {body}')
    message_content = body['message_content']
    user_id = body['user_id']
    session_id = body['session_id']
    history = body['history']

    print(f'History: {history}')

    self.__save_message(user_id, session_id, "USER", message_content)

    completion = self.__generate(message_content, history)

    self.__save_message(user_id, session_id, "AI", completion)

    return build_response(200, { "body": completion })
  
  def __generate(self, message_content, history):
    try: 
      completion = self.__openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            *self.__format_history(history),
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
  
  def __format_history(self, history):
      formatted = []
      for message in history:
          role = message['message_type'].lower()
          if role == 'ai':
            role = 'assistant'
          formatted.append({
              "role": role,
              "content": message['message_content']
          })
      return formatted
  
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