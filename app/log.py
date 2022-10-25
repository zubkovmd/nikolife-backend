"""Logging configuration for service"""

import logging

from typing import List

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
)


class Logger:
    """Default logger class"""
    def __init__(self, name: str):
        """Logger instance initializer"""
        self.name: str = name
        self.logger: logging.Logger = logging.getLogger(name)


class Loggers:
    """Named loggers container"""
    loggers: List[Logger] = []

    @classmethod
    def get_logger(cls, name) -> Logger:
        """
        Return named logger if exists, else first creates logger with this name

        :param name: logger name
        :return: named logger
        """
        named_logger = list(filter(lambda x: x.name == name, cls.loggers))
        if named_logger:
            return named_logger[0].logger
        else:
            new_logger = Logger(name)
            cls.loggers.append(Logger(name))
            return new_logger.logger


default_logger = Loggers.get_logger("SERVER_MESSAGE")
