from utils import *

class Router:
  def __init__(self, logger, completions_handler, sessions_handler):
    self.__logger = logger
    self.__completions_handler = completions_handler
    self.__sessions_handler = sessions_handler

  def handle_request(self, method, path, body):
    if path.startswith(completions_path):
      return self.__completions_handler.handle(method, path, body)
    if path.startswith(sessions_path):
      return self.__sessions_handler.handle(method, path, body)
      