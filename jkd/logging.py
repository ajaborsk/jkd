
import logging

logger = logging.getLogger(__name__)


def debug(*args):
    logger.debug(*args)

def warning(*args):
    logger.warning(*args)

def info(*args):
    logger.info(*args)

def error(*args):
    logger.error(*args)
