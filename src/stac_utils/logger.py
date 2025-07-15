import datetime
import json
import logging
import os

STANDARD_LOG_RECORD_FIELDS = [
    'name', 'msg', 'args', 'levelname', 'levelno',
    'pathname', 'filename', 'module', 'exc_info',
    'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated',
    'thread', 'threadName', 'processName', 'process',
    'message', 'state', 'taskName'
]

class StacSysLogFormatter(logging.Formatter):
    def __init__(self, default_fmt, datefmt=None):
        super().__init__(fmt=default_fmt, datefmt=datefmt, style='{')
        self.default_fmt = default_fmt
        self.datefmt = datefmt

    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created)
        return ct.strftime(datefmt or self.datefmt or "%Y-%m-%d %H:%M:%S.%3f")[:-3]
    
    def format(self, record):

        record.asctime = self.formatTime(record, self.datefmt)
        record.message = record.getMessage()

        if record.state:
            self._style._fmt = (
                "[{levelname}: {asctime}] {state}: {message}"
            )
        else:
            self._style._fmt = (
                "[{levelname}: {asctime}] {message}"
            )

        return super().format(record)


class StacJsonFormatter(logging.Formatter):
    def format(self, record):

        log_time = datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat()

        log_record = {
            'timestamp': log_time,
            'level': record.levelname,
            'message': record.getMessage(),
            'filename': record.filename,
            'line': record.lineno,
            'function': record.funcName,
            'state': record.state
        }

        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in STANDARD_LOG_RECORD_FIELDS and not k.startswith("_")
        }

        return json.dumps({**log_record, **extras})
    

class StacLogFilter(logging.Filter):

    def __init__(self, env_var_name, field_name = None, default = "unknown"):
        super().__init__()
        self.env_var_name = env_var_name
        self.field_name = field_name or env_var_name.lower()
        self.default = default

    def filter(self, record) -> bool:
        setattr(record, self.field_name, os.getenv(self.env_var_name, self.default))
        return True


def configure_logger(stage: str = None, formatter: logging.Formatter = None) -> logging.Logger:

    log_stage = stage or os.getenv('STAGE', 'dev').lower()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False 

    logger.handlers.clear()

    if not formatter:
            
        if log_stage == "production":
            formatter = StacJsonFormatter()
        else:
            formatter = StacSysLogFormatter(
                default_fmt="",
                datefmt='%H:%M:%S.%f'
            )

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        console_handler.addFilter(StacLogFilter(env_var_name = "STATE", default = 'XX'))

        logger.addHandler(console_handler)

    return logger


def get_default_logger() -> logging.Logger:
    return configure_logger()


if __name__ == "__main__":
    logger = get_default_logger()

    logger.info('testing this thing')    