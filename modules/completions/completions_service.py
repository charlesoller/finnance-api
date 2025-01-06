from utils import build_response
class CompletionsService:
  def __init__(self, logger, db, client):
    self.__logger = logger
    self.__db = db
    self.__client = client

  def get_all(self):
    return build_response(200, { 'Message': 'Success! Here are all of the completions...' })
  
  def generate(self, body):
    self.__logger.info(body)
    try: 
      completion = self.__client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": body['message']
            }
        ]
      )

      response = completion.choices[0].message.content
      self.__logger.info(f'Completion: {str(response)}')
    except Exception as e: 
      raise Exception(f'Failed to generate completion: {str(e)}')
    
    return build_response(200, { 'body': response })