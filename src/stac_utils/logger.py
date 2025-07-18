"""
Custom logging utilities for stac code.

The module includes:
- StacSysLogFormatter:  Human-readable console logging with state information
- StacJsonFormatter:    Structured JSON logging, intended for DataDog
- StacLogFilter:        Filter for adding environment variables to log records
- StateLogFilter:       Specialized filter for adding state information to logs
- configure_logger:     Setting up loggers with appropriate formatters

Example:
    Basic usage:
    >>> logger = configure_logger()
    >>> logger.info("Processing a log item")
    
    Production usage:
    >>> assumes os.getenv('STAGE') returns 'production'
    >>> logger = configure_logger()
    >>> logger.info("DataDog logs updated")
"""

from datetime import datetime, timezone
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
    """
        Logging formatter ideal for producing human readable logs to sys.out including a level name, state (if provided), and message.
    """
    def __init__(self, default_fmt, datefmt=None):
        super().__init__(fmt=default_fmt, datefmt=datefmt, style='{')
        self.default_fmt = default_fmt
        self.datefmt = datefmt

    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created)

        if datefmt or self.datefmt:
            return ct.strftime(datefmt or self.datefmt)
        else:
            return ct.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
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
    """
        Logging formatter ideal for producing JSON parsable logs including state and some stac-specific fields. Intended to be useful for DataDog log ingestion and parsing.
    """
        
    def format(self, record):

        log_time = datetime.fromtimestamp(record.created, timezone.utc).isoformat()

        log_record = {
            'timestamp': log_time,
            'level': record.levelname,
            'message': record.getMessage(),
            'stac': {
                'filename': record.filename,
                'line': record.lineno,
                'function': record.funcName,
                'message': record.getMessage(),
            },
            'state': record.state
        }

        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in STANDARD_LOG_RECORD_FIELDS and not k.startswith("_")
        }

        return json.dumps({**log_record, **extras})
    

class StacLogFilter(logging.Filter):
    """
        Generic filter to pull an environment variable into logs for use.
    """

    def __init__(self, env_var_name, field_name = None, default = "unknown"):
        super().__init__()
        self.env_var_name = env_var_name
        self.field_name = field_name or env_var_name.lower()
        self.default = default

    def filter(self, record) -> bool:
        setattr(record, self.field_name, os.getenv(self.env_var_name, self.default))
        return True
    
class StateLogFilter(StacLogFilter):
    """
        Extends StacLogFilter to pull STATE environment information into logs for use. 
    """

    def __init__(self):
        super().__init__(env_var_name = "STATE", default = "XX")

    def filter(self, record) -> bool:
        state = os.getenv(self.env_var_name, self.default)

        setattr(record, self.field_name, state.upper() if state else self.default)
        return True


def configure_logger(
        stage: str = None, 
        sys_formatter: StacSysLogFormatter = None, 
        json_Formatter: StacJsonFormatter = None,
        filters: list[StacLogFilter] = []
    ) -> logging.Logger:
    """
        Configure and return a logger with appropriate formatters and filters.
        
        Args:
            stage (str, optional): Deployment stage ("production" or other).
                if None, reads from STAGE environment variable (default: "dev")
            sys_formatter (StacSysLogFormatter, optional): Custom system formatter.
                if None, creates default formatter for non-production stages
            json_Formatter (StacJsonFormatter, optional): Custom JSON formatter.
                if None, creates default formatter for production stage
            filters (list[StacLogFilter], optional): Additional filters to apply.
                StateLogFilter is always added automatically
        
        Returns:
            logging.Logger: Configured logger instance
    """

    log_stage = stage or os.getenv('STAGE', 'dev').lower()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False 

    if log_stage == "production":
        formatter = json_Formatter or StacJsonFormatter()
    else:
        formatter = sys_formatter or StacSysLogFormatter(
                default_fmt="",
                datefmt='%H:%M:%S.%f'
            )
        
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        console_handler.addFilter(StateLogFilter())

        for filter in filters:
            console_handler.addFilter(filter)

        logger.addHandler(console_handler)

    return logger