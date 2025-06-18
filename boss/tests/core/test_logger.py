import os
import logging
from boss.core.logger import get_logger, LOG_FILE

def test_logger_initialization(tmp_path, monkeypatch):
    # Patch log file location
    log_dir = tmp_path / "logs"
    log_file = log_dir / "boss.log"
    monkeypatch.setattr("boss.core.logger.LOG_DIR", str(log_dir))
    monkeypatch.setattr("boss.core.logger.LOG_FILE", str(log_file))

    logger = get_logger("TEST", level=logging.DEBUG)
    logger.info("Test log entry")
    logger.error("Test error entry")
    logger.handlers[0].flush()
    assert os.path.exists(log_file)
    with open(log_file) as f:
        content = f.read()
        assert "Test log entry" in content
        assert "Test error entry" in content
