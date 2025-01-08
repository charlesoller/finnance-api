import re
from utils import *

class SessionsHandler:
    def __init__(self, logger, sessions_service):
        self.__logger = logger
        self.__sessions_service = sessions_service

    def __extract_path(self, path):
      base = sessions_path
      if path == base:
        return "/"  
      elif path.startswith(base):
        return path[len(base):]
      return path

    def handle(self, method, path, body):
        subpath = self.__extract_path(path)

        if method == get_request:
            if subpath == "/":
              return self.__sessions_service.get_all() # Not yet implemented
            
            # The following is certainly a fragile way to match that will have to be more robust in the future
            elif re.fullmatch(r"[a-f0-9\-]{36}", subpath[1:]): 
              return self.__sessions_service.get_by_id(subpath[1:])

        raise Exception(f"No matching path found for method={method}, path={path}")
