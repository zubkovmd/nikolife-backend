"""Logging configuration for service"""

import logging

from typing import List

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
)


class _Logger:
    """Default logger class"""
    def __init__(self, name: str):
        """Logger instance initializer"""
        self.name: str = name
        self.logger: logging.Logger = logging.getLogger(name)


class Loggers:
    """Named loggers container"""
    loggers: List[_Logger] = []

    @classmethod
    def get_named_logger(cls, name) -> logging.Logger:
        """
        Return named logger if exists, else first creates logger with this name

        :param name: logger name
        :return: named logger
        """
        named_logger = list(filter(lambda x: x.name == name, cls.loggers))
        if named_logger:
            return named_logger[0].logger
        else:
            new_logger = _Logger(name)
            cls.loggers.append(_Logger(name))
            return new_logger.logger

    @classmethod
    def get_default_logger(cls):
        """
                Return default logger if exists, else first creates logger with this name

                :param name: logger name
                :return: named logger
                """
        DEFAULT_LOGGER_NAME = "DEFAULT"
        named_logger = list(filter(lambda x: x.name == DEFAULT_LOGGER_NAME, cls.loggers))
        if named_logger:
            return named_logger[0].logger
        else:
            new_logger = _Logger(DEFAULT_LOGGER_NAME)
            cls.loggers.append(_Logger(DEFAULT_LOGGER_NAME))
            return new_logger.logger


default_logger = Loggers.get_named_logger("SERVER_MESSAGE")
