import pytest
import logging
from unittest.mock import Mock, patch
from src.stac_utils.logger import StacSysLogFormatter  # Replace with actual import


class TestStacSysLogFormatter:
    
    @pytest.fixture
    def formatter(self):
        """Basic formatter instance for testing."""
        return StacSysLogFormatter(default_fmt="[{levelname}: {asctime}] {message}")
    
    @pytest.fixture
    def formatter_with_datefmt(self):
        """Formatter with custom date format."""
        return StacSysLogFormatter(
            default_fmt="[{levelname}: {asctime}] {message}",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    @pytest.fixture
    def mock_record(self):
        """Mock log record for testing."""
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456  # 2022-01-01 00:00:00.123456
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.state = None
        # Add required attributes for logging.Formatter
        record.name = "test_logger"
        record.msg = "Test message"
        record.args = ()
        record.levelno = logging.INFO
        record.pathname = "test.py"
        record.filename = "test.py"
        record.module = "test"
        record.lineno = 1
        record.funcName = "test_function"
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return record
    
    @pytest.fixture
    def mock_record_with_state(self):
        """Mock log record with state attribute."""
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "ERROR"
        record.getMessage.return_value = "Test error message"
        record.state = "PROCESSING"
        # Add required attributes for logging.Formatter
        record.name = "test_logger"
        record.msg = "Test error message"
        record.args = ()
        record.levelno = logging.ERROR
        record.pathname = "test.py"
        record.filename = "test.py"
        record.module = "test"
        record.lineno = 1
        record.funcName = "test_function"
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return record
    
    def test_init_default_format(self):
        """Test formatter initialization with default format."""
        default_fmt = "[{levelname}: {asctime}] {message}"
        formatter = StacSysLogFormatter(default_fmt)
        
        assert formatter.default_fmt == default_fmt
        assert formatter.datefmt is None
        assert formatter._style._fmt == default_fmt
    
    def test_init_with_datefmt(self):
        """Test formatter initialization with custom date format."""
        default_fmt = "[{levelname}: {asctime}] {message}"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = StacSysLogFormatter(default_fmt, datefmt)
        
        assert formatter.default_fmt == default_fmt
        assert formatter.datefmt == datefmt
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_time_default(self, mock_datetime, formatter):
        """Test formatTime with default date format."""
        # Mock datetime to return a predictable result
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        record = Mock()
        record.created = 1640995200.123456
        
        result = formatter.formatTime(record)
        
        # Should use default format and truncate to 3 decimal places
        mock_datetime.fromtimestamp.assert_called_once_with(1640995200.123456)
        mock_dt.strftime.assert_called_once_with("%Y-%m-%d %H:%M:%S.%f")
        assert result == "2022-01-01 00:00:00.123"
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_time_custom_datefmt(self, mock_datetime, formatter_with_datefmt):
        """Test formatTime with custom date format."""
        # Mock datetime to return a predictable result
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        record = Mock()
        record.created = 1640995200.123456
        
        result = formatter_with_datefmt.formatTime(record)
        
        mock_datetime.fromtimestamp.assert_called_once_with(1640995200.123456)
        mock_dt.strftime.assert_called_once_with("%Y-%m-%d %H:%M:%S")
        assert result == "2022-01-01 00:00:00"
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_time_with_parameter(self, mock_datetime, formatter):
        """Test formatTime with datefmt parameter."""
        # Mock datetime to return a predictable result
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022/01/01 00:00"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        record = Mock()
        record.created = 1640995200.123456
        custom_fmt = "%Y/%m/%d %H:%M"
        
        result = formatter.formatTime(record, custom_fmt)
        
        mock_datetime.fromtimestamp.assert_called_once_with(1640995200.123456)
        mock_dt.strftime.assert_called_once_with(custom_fmt)
        assert result == "2022/01/01 00:00"
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_time_datetime_mock(self, mock_datetime, formatter):
        """Test formatTime with mocked datetime."""
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 12:34:56.789000"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        record = Mock()
        record.created = 1640995200.123456
        
        result = formatter.formatTime(record)
        
        mock_datetime.fromtimestamp.assert_called_once_with(1640995200.123456)
        mock_dt.strftime.assert_called_once_with("%Y-%m-%d %H:%M:%S.%f")
        assert result == "2022-01-01 12:34:56.789"
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_without_state(self, mock_datetime, formatter, mock_record):
        """Test format method with record that has no state."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        mock_record.state = None
        
        result = formatter.format(mock_record)
        
        # Should use format without state
        assert "[INFO: 2022-01-01 00:00:00.123] Test message" in result
        assert "state" not in result.lower()
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_with_state(self, mock_datetime, formatter, mock_record_with_state):
        """Test format method with record that has state."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        result = formatter.format(mock_record_with_state)
        
        # Should use format with state
        assert "[ERROR: 2022-01-01 00:00:00.123] PROCESSING: Test error message" in result
        assert "PROCESSING" in result
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_with_falsy_state(self, mock_datetime, formatter, mock_record):
        """Test format method with falsy state values."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        falsy_states = [None, "", 0, False, []]
        
        for state in falsy_states:
            mock_record.state = state
            # Reset the mock to avoid stale calls
            mock_record.getMessage.return_value = "Test message"
            result = formatter.format(mock_record)
            
            # Should use format without state for falsy values
            assert "[INFO: 2022-01-01 00:00:00.123] Test message" in result
            assert "state" not in result.lower()
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_with_truthy_state(self, mock_datetime, formatter, mock_record):
        """Test format method with various truthy state values."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        truthy_states = ["ACTIVE", "processing", 1, True, ["item"]]
        
        for state in truthy_states:
            mock_record.state = state
            # Reset the mock to avoid stale calls
            mock_record.getMessage.return_value = "Test message"
            result = formatter.format(mock_record)
            
            # Should use format with state for truthy values
            assert f"[INFO: 2022-01-01 00:00:00.123] {state}: Test message" in result
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_modifies_record_attributes(self, mock_datetime, formatter, mock_record):
        """Test that format method sets required attributes on record."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        formatter.format(mock_record)
        
        # Check that asctime and message are set
        assert hasattr(mock_record, 'asctime')
        assert hasattr(mock_record, 'message')
        assert mock_record.asctime == "2022-01-01 00:00:00.123"
        assert mock_record.message == "Test message"
    
    def test_format_calls_super_format(self, formatter, mock_record):
        """Test that format method calls parent format method."""
        with patch.object(logging.Formatter, 'format', return_value="formatted_output") as mock_super:
            result = formatter.format(mock_record)
            
            mock_super.assert_called_once_with(mock_record)
            assert result == "formatted_output"
    
    def test_format_changes_style_fmt(self, formatter, mock_record):
        """Test that format method changes the style format string."""      
        # Test without state
        mock_record.state = None
        formatter.format(mock_record)
        expected_fmt_no_state = "[{levelname}: {asctime}] {message}"
        assert formatter._style._fmt == expected_fmt_no_state
        
        # Test with state
        mock_record.state = "PROCESSING"
        formatter.format(mock_record)
        expected_fmt_with_state = "[{levelname}: {asctime}] {state}: {message}"
        assert formatter._style._fmt == expected_fmt_with_state
    
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_multiple_format_calls(self, mock_datetime, formatter):
        """Test that formatter works correctly with multiple format calls."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        # First call without state
        record1 = Mock(spec=logging.LogRecord)
        record1.created = 1640995200.123456
        record1.levelname = "INFO"
        record1.getMessage.return_value = "First message"
        record1.state = None
        # Add required attributes
        record1.name = "test_logger"
        record1.msg = "First message"
        record1.args = ()
        record1.levelno = logging.INFO
        record1.pathname = "test.py"
        record1.filename = "test.py"
        record1.module = "test"
        record1.lineno = 1
        record1.funcName = "test_function"
        record1.exc_info = None
        record1.exc_text = None
        record1.stack_info = None
        
        # Second call with state
        record2 = Mock(spec=logging.LogRecord)
        record2.created = 1640995200.123456
        record2.levelname = "ERROR"
        record2.getMessage.return_value = "Second message"
        record2.state = "FAILED"
        # Add required attributes
        record2.name = "test_logger"
        record2.msg = "Second message"
        record2.args = ()
        record2.levelno = logging.ERROR
        record2.pathname = "test.py"
        record2.filename = "test.py"
        record2.module = "test"
        record2.lineno = 1
        record2.funcName = "test_function"
        record2.exc_info = None
        record2.exc_text = None
        record2.stack_info = None
        
        result1 = formatter.format(record1)
        result2 = formatter.format(record2)
        
        assert "[INFO: 2022-01-01 00:00:00.123] First message" in result1
        assert "[ERROR: 2022-01-01 00:00:00.123] FAILED: Second message" in result2


# Additional integration tests
class TestStacSysLogFormatterIntegration:
    """Integration tests with real logging."""
    
    def test_with_real_logger(self):
        """Test formatter with actual logger."""
        logger = logging.getLogger('test_logger')
        logger.setLevel(logging.INFO)
        
        # Create handler with custom formatter
        handler = logging.StreamHandler()
        formatter = StacSysLogFormatter("[{levelname}: {asctime}] {message}")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Create a log record
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.state = "ACTIVE"
        
        # This should not raise an exception
        formatted = formatter.format(record)
        assert "ACTIVE" in formatted
        assert "Test message" in formatted
        
        # Clean up
        logger.removeHandler(handler)


# Parametrized tests for edge cases
class TestStacSysLogFormatterEdgeCases:
    
    @pytest.mark.parametrize("timestamp,expected_time", [
        (1640995200.0, "000"),
        (1640995200.999, "999"),
        (1640995200.123456789, "123"),
    ])
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_time_precision(self, mock_datetime, timestamp, expected_time):
        """Test formatTime with different timestamp precisions."""
        # Mock datetime to return different precision values
        mock_dt = Mock()
        if timestamp == 1640995200.0:
            mock_dt.strftime.return_value = "2022-01-01 00:00:00.000000"
        elif timestamp == 1640995200.999:
            mock_dt.strftime.return_value = "2022-01-01 00:00:00.999000"
        else:  # 1640995200.123456789
            mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        formatter = StacSysLogFormatter("[{levelname}: {asctime}] {message}")
        record = Mock()
        record.created = timestamp
        
        result = formatter.formatTime(record)
        assert result.endswith(expected_time)
        assert result.startswith("2022-01-01 00:00:00.")
    
    @pytest.mark.parametrize("state_value", [
        "NORMAL_STATE",
        "state with spaces",
        "STATE_WITH_UNDERSCORES",
        "123",
        "mixed123State",
    ])
    @patch('src.stac_utils.logger.datetime')  # Replace with actual module path
    def test_format_with_various_state_strings(self, mock_datetime, state_value):
        """Test format with different state string values."""
        # Mock datetime for predictable time formatting
        mock_dt = Mock()
        mock_dt.strftime.return_value = "2022-01-01 00:00:00.123456"
        mock_datetime.fromtimestamp.return_value = mock_dt
        
        formatter = StacSysLogFormatter("[{levelname}: {asctime}] {message}")
        record = Mock(spec=logging.LogRecord)
        record.created = 1640995200.123456
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.state = state_value
        # Add required attributes for logging.Formatter
        record.name = "test_logger"
        record.msg = "Test message"
        record.args = ()
        record.levelno = logging.INFO
        record.pathname = "test.py"
        record.filename = "test.py"
        record.module = "test"
        record.lineno = 1
        record.funcName = "test_function"
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        
        result = formatter.format(record)
        assert f"{state_value}: Test message" in result