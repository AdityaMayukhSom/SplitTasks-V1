import logging


logger: logging.Logger = logging.getLogger("uvicorn")
logger.setLevel(level=logging.getLevelName(logging.DEBUG))
