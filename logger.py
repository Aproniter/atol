import logging


_log_format = f'''%(asctime)s - [%(levelname)s] - %(name)s - 
(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'''


class Logger:
    """Класс настройки логирования"""

    def __init__(self, name, filename, log_format=_log_format):
        self.name = name
        self.filename = filename
        self.log_format = log_format

    def _get_file_handler(self):
        file_handler = logging.FileHandler(f'{self.filename}.log')
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter(self.log_format))
        return file_handler

    def _get_stream_handler(self):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter(self.log_format))
        return stream_handler

    def get_logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler())
        logger.addHandler(self._get_stream_handler())
        return logger