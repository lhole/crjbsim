import logging
from logging import FileHandler, Handler, StreamHandler

from crjbsim import time_provider


class DESAwareHandlerMixin(Handler):
    def format(self, record: logging.LogRecord) -> str:
        return f"{time_provider.get_time_formatted()} {super().format(record)}"


class DESAwareStreamHandler(StreamHandler, DESAwareHandlerMixin):
    pass


class DESAwareFileHandler(FileHandler, DESAwareHandlerMixin):
    pass


def setup() -> None:
    root_logger = logging.getLogger()
    handler = DESAwareStreamHandler()
    handler.formatter = logging.Formatter('%(levelname)-8s: %(message)s (%(name)s)')
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG)
