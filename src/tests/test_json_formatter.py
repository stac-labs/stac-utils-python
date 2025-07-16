import pytest
import json
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from src.stac_utils.logger import StacJsonFormatter  # Replace with actual import


STANDARD_LOG_RECORD_FIELDS = [
    'name', 'msg', 'args', 'levelname', 'levelno',
    'pathname', 'filename', 'module', 'exc_info',
    'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated',
    'thread', 'threadName', 'processName', 'process',
    'message', 'state', 'taskName'
]

class TestStacJsonFormatter:
    
    @pytest.fixture
    def formatter(self):
        """Basic formatter instance for testing."""
        return StacJsonFormatter()
    
    @pytest.fixture
    def mock_record(self):
        """Mock log record for testing."""
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456  # 2022-01-01 00:00:00.123456 UTC
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.filename = "test.py"
        record.lineno = 42
        record.funcName = "test_function"
        record.state = "ACTIVE"
        # Add standard LogRecord attributes
        record.name = "test_logger"
        record.msg = "Test message"
        record.args = ()
        record.levelno = logging.INFO
        record.pathname = "/path/to/test.py"
        record.module = "test"
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        record.thread = 12345
        record.threadName = "MainThread"
        record.process = 67890
        record.processName = "MainProcess"
        record.relativeCreated = 1000.0
        record.msecs = 123.456
        return record
    
    @pytest.fixture
    def mock_record_with_extras(self):
        """Mock log record with extra fields."""
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "ERROR"
        record.getMessage.return_value = "Error message"
        record.filename = "error.py"
        record.lineno = 100
        record.funcName = "error_function"
        record.state = "FAILED"
        # Standard attributes
        record.name = "error_logger"
        record.msg = "Error message"
        record.args = ()
        record.levelno = logging.ERROR
        record.pathname = "/path/to/error.py"
        record.module = "error"
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        record.thread = 12345
        record.threadName = "MainThread"
        record.process = 67890
        record.processName = "MainProcess"
        record.relativeCreated = 2000.0
        record.msecs = 456.789
        # Extra fields
        record.user_id = "user123"
        record.request_id = "req456"
        record.custom_field = "custom_value"
        return record
    
    def test_format_basic_structure(self, formatter, mock_record):
        """Test basic JSON structure and required fields."""
        result = formatter.format(mock_record)
        
        # Should return valid JSON
        log_data = json.loads(result)
        
        # Check required top-level fields
        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'message' in log_data
        assert 'stac' in log_data
        assert 'state' in log_data
        
        # Check stac nested structure
        stac_data = log_data['stac']
        assert 'filename' in stac_data
        assert 'line' in stac_data
        assert 'function' in stac_data
        assert 'message' in stac_data
    
    def test_format_field_values(self, formatter, mock_record):
        """Test that field values are correctly mapped."""
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # Check top-level values
        assert log_data['level'] == "INFO"
        assert log_data['message'] == "Test message"
        assert log_data['state'] == "ACTIVE"
        
        # Check stac nested values
        stac_data = log_data['stac']
        assert stac_data['filename'] == "test.py"
        assert stac_data['line'] == 42
        assert stac_data['function'] == "test_function"
        assert stac_data['message'] == "Test message"
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_timestamp_utc(self, mock_datetime, formatter, mock_record):
        """Test timestamp formatting in UTC."""
        # Mock datetime to return predictable result
        mock_dt = Mock()
        mock_dt.isoformat.return_value = "2022-01-01T00:00:00.123456+00:00"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # Verify UTC timezone is used
        mock_datetime.fromtimestamp.assert_called_once_with(1640995200.123456, timezone.utc)
        mock_dt.isoformat.assert_called_once()
        assert log_data['timestamp'] == "2022-01-01T00:00:00.123456+00:00"
    
    def test_format_with_none_state(self, formatter, mock_record):
        """Test formatting when state is None."""
        mock_record.state = None
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        assert log_data['state'] is None
    
    def test_format_with_extra_fields(self, formatter, mock_record_with_extras):
        """Test that extra fields are included in output."""
        result = formatter.format(mock_record_with_extras)
        log_data = json.loads(result)
        
        # Check that extra fields are included
        assert log_data['user_id'] == "user123"
        assert log_data['request_id'] == "req456"
        assert log_data['custom_field'] == "custom_value"
        
        # Check that standard fields are still present
        assert log_data['level'] == "ERROR"
        assert log_data['message'] == "Error message"
        assert log_data['state'] == "FAILED"
    
    def test_format_excludes_standard_fields(self, formatter, mock_record):
        """Test that standard log record fields are excluded from extras."""
        # Add some standard fields that should be excluded
        mock_record.name = "test_logger"
        mock_record.levelno = logging.INFO
        mock_record.pathname = "/path/to/test.py"
        mock_record.module = "test"
        mock_record.exc_info = None
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # These standard fields should not appear as extras
        assert 'name' not in log_data or log_data.get('name') is None
        assert 'levelno' not in log_data or log_data.get('levelno') is None
        assert 'pathname' not in log_data or log_data.get('pathname') is None
        assert 'module' not in log_data or log_data.get('module') is None
        assert 'exc_info' not in log_data or log_data.get('exc_info') is None
    
    def test_format_excludes_private_fields(self, formatter, mock_record):
        """Test that private fields (starting with _) are excluded."""
        # Add private fields that should be excluded
        mock_record._private_field = "should_be_excluded"
        mock_record.__very_private = "also_excluded"
        mock_record.public_field = "should_be_included"
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # Private fields should not appear
        assert '_private_field' not in log_data
        assert '__very_private' not in log_data
        # Public field should appear
        assert log_data['public_field'] == "should_be_included"
    
    def test_format_returns_valid_json(self, formatter, mock_record):
        """Test that output is always valid JSON."""
        result = formatter.format(mock_record)
        
        # Should not raise exception
        log_data = json.loads(result)
        
        # Should be a dictionary
        assert isinstance(log_data, dict)
    
    def test_format_with_complex_extra_values(self, formatter, mock_record):
        """Test formatting with complex data types in extra fields."""
        mock_record.list_field = [1, 2, 3]
        mock_record.dict_field = {"nested": "value"}
        mock_record.bool_field = True
        mock_record.int_field = 42
        mock_record.float_field = 3.14
        mock_record.none_field = None
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # Check that complex types are preserved
        assert log_data['list_field'] == [1, 2, 3]
        assert log_data['dict_field'] == {"nested": "value"}
        assert log_data['bool_field'] is True
        assert log_data['int_field'] == 42
        assert log_data['float_field'] == 3.14
        assert log_data['none_field'] is None
    
    def test_format_with_different_log_levels(self, formatter):
        """Test formatting with different log levels."""
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL")
        ]
        
        for level_num, level_name in levels:
            record = Mock(spec=logging.LogRecord)
            record.created = 1640995200.123456
            record.levelname = level_name
            record.levelno = level_num
            record.getMessage.return_value = f"Test {level_name} message"
            record.filename = "test.py"
            record.lineno = 10
            record.funcName = "test_func"
            record.state = "TESTING"
            
            result = formatter.format(record)
            log_data = json.loads(result)
            
            assert log_data['level'] == level_name
            assert log_data['message'] == f"Test {level_name} message"
    
    def test_format_calls_get_message(self, formatter, mock_record):
        """Test that format calls record.getMessage()."""
        mock_record.getMessage.return_value = "Dynamic message"
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # Should call getMessage() for both top-level and stac message
        assert mock_record.getMessage.call_count >= 2
        assert log_data['message'] == "Dynamic message"
        assert log_data['stac']['message'] == "Dynamic message"
    
    def test_format_with_message_args(self, formatter):
        """Test formatting with message arguments."""
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "INFO"
        record.msg = "Hello %s, you have %d messages"
        record.args = ("Alice", 5)
        record.getMessage.return_value = "Hello Alice, you have 5 messages"
        record.filename = "test.py"
        record.lineno = 20
        record.funcName = "test_func"
        record.state = "PROCESSING"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data['message'] == "Hello Alice, you have 5 messages"
        assert log_data['stac']['message'] == "Hello Alice, you have 5 messages"
    
    def test_format_preserves_extra_field_order(self, formatter, mock_record):
        """Test that extra fields are included alongside standard fields."""
        mock_record.extra1 = "value1"
        mock_record.extra2 = "value2"
        mock_record.extra3 = "value3"
        
        result = formatter.format(mock_record)
        log_data = json.loads(result)
        
        # All extra fields should be present
        assert log_data['extra1'] == "value1"
        assert log_data['extra2'] == "value2"
        assert log_data['extra3'] == "value3"
        
        # Standard fields should still be present
        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'message' in log_data
        assert 'stac' in log_data
        assert 'state' in log_data


# Test with different STANDARD_LOG_RECORD_FIELDS configurations
class TestStacJsonFormatterWithDifferentStandardFields:

    @pytest.fixture
    def formatter(self):
        """Basic formatter instance for testing."""
        return StacJsonFormatter()
    
    def test_format_with_custom_standard_fields(self, formatter):
        """Test behavior with different STANDARD_LOG_RECORD_FIELDS."""
        # This test assumes STANDARD_LOG_RECORD_FIELDS is defined
        # You might need to adjust based on your actual implementation
        
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.filename = "test.py"
        record.lineno = 30
        record.funcName = "test_func"
        record.state = "ACTIVE"
        
        # Add some fields that might or might not be in STANDARD_LOG_RECORD_FIELDS
        record.name = "test_logger"
        record.custom_field = "custom_value"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        # custom_field should appear since it's not in standard fields
        assert log_data['custom_field'] == "custom_value"


# Integration tests
class TestStacJsonFormatterIntegration:
    
    def test_with_real_logger(self):
        """Test formatter with actual logger."""
        logger = logging.getLogger('test_json_logger')
        logger.setLevel(logging.INFO)
        
        # Create a list to capture formatted output
        formatted_outputs = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                formatted_outputs.append(self.format(record))
        
        handler = TestHandler()
        formatter = StacJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Create a log record with state attribute
        record = logging.LogRecord(
            name='test_json_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=50,
            msg='Integration test message',
            args=(),
            exc_info=None
        )
        record.state = "INTEGRATION_TEST"
        
        # Emit the record
        logger.handle(record)
        
        # Check the output
        assert len(formatted_outputs) == 1
        log_data = json.loads(formatted_outputs[0])
        
        assert log_data['level'] == "INFO"
        assert log_data['message'] == "Integration test message"
        assert log_data['state'] == "INTEGRATION_TEST"
        assert log_data['stac']['filename'] == "test.py"
        assert log_data['stac']['line'] == 50
        
        # Clean up
        logger.removeHandler(handler)


# Parametrized tests for edge cases
class TestStacJsonFormatterEdgeCases:

    @pytest.fixture
    def formatter(self):
        """Basic formatter instance for testing."""
        return StacJsonFormatter()
    
    @pytest.fixture
    def mock_record(self):
        """Mock log record for testing."""
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456  # 2022-01-01 00:00:00.123456 UTC
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.filename = "test.py"
        record.lineno = 42
        record.funcName = "test_function"
        record.state = "ACTIVE"
        # Add standard LogRecord attributes
        record.name = "test_logger"
        record.msg = "Test message"
        record.args = ()
        record.levelno = logging.INFO
        record.pathname = "/path/to/test.py"
        record.module = "test"
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        record.thread = 12345
        record.threadName = "MainThread"
        record.process = 67890
        record.processName = "MainProcess"
        record.relativeCreated = 1000.0
        record.msecs = 123.456
        return record
    
    @pytest.mark.parametrize("state_value", [
        None,
        "",
        "NORMAL_STATE",
        "state with spaces",
        123,
        True,
        False,
        [],
        {},
    ])
    def test_format_with_various_state_values(self, state_value):
        """Test format with different state value types."""
        formatter = StacJsonFormatter()
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.filename = "test.py"
        record.lineno = 60
        record.funcName = "test_func"
        record.state = state_value
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data['state'] == state_value
    
    @pytest.mark.parametrize("extra_field,extra_value", [
        ("string_field", "string_value"),
        ("int_field", 42),
        ("float_field", 3.14),
        ("bool_field", True),
        ("list_field", [1, 2, 3]),
        ("dict_field", {"key": "value"}),
        ("none_field", None),
    ])
    def test_format_with_various_extra_field_types(self, extra_field, extra_value):
        """Test format with different extra field types."""
        formatter = StacJsonFormatter()
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.filename = "test.py"
        record.lineno = 70
        record.funcName = "test_func"
        record.state = "TESTING"
        
        # Add the extra field
        setattr(record, extra_field, extra_value)
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data[extra_field] == extra_value
    
    def test_format_with_non_json_serializable_extra(self, formatter, mock_record):
        """Test behavior with non-JSON serializable extra fields."""

        # Add a non-serializable field
        mock_record.datetime_field = datetime.now()
        
        # This should raise a TypeError when trying to serialize
        with pytest.raises(TypeError):
            formatter.format(mock_record)