from utils import *

class CompletionsHandler:
  def __init__(self, logger, completions_service):
    self.__logger = logger
    self.__completions_service = completions_service

  def __extract_path(self, path):
    base = completions_path
    if path == base:
      return "/"  
    elif path.startswith(base):
      return path[len(base):]
    return path
  
  def handle(self, method, path, body):
    self.__logger.info("Method: %s", method)
    self.__logger.info("Path: %s", path)
    subpath = self.__extract_path(path)
    self.__logger.info("Subpath: %s", subpath)

    if method == get_request:
      if subpath == '/':
        return self.__completions_service.get_all()
    elif method == post_request:
      if subpath == '/':
        return self.__completions_service.generate(body)
      
    raise Exception("No matching path found in CompletionsHandler")