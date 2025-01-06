from utils import *

class Router:
  def __init__(self, logger, completions_handler):
    self.__logger = logger
    self.__completions_handler = completions_handler

  def handle_request(self, method, path, body):
    if completions_path in path:
      return self.__completions_handler.handle(method, path, body)
      