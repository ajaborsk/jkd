
import logging

logger_main = logging.getLogger("main")
logger_msg = logging.getLogger("msg")


def debug(*args):
    logger_main.debug(*args)

def warning(*args):
    logger_main.warning(*args)

def info(*args):
    logger_main.info(*args)

def error(*args):
    logger_main.error(*args)
