import os
import logging
from boss.core.logger import get_logger

def test_logger_initialization(tmp_path, monkeypatch):
    # Patch log file location to boss/logs/boss.log
    log_dir = tmp_path / "boss" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "boss.log"
    monkeypatch.setattr("boss.core.logger.LOG_DIR", str(log_dir))
    monkeypatch.setattr("boss.core.logger.LOG_FILE", str(log_file))

    logger = get_logger("TEST", level=logging.DEBUG)
    logger.info("Test log entry")
    logger.error("Test error entry")
    for handler in logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    assert os.path.exists(log_file)
    with open(log_file) as f:
        content = f.read()
        assert "Test log entry" in content
        assert "Test error entry" in content

    # Test log rotation
    for i in range(2000):
        logger.info(f"Filler {i}")
    logger.handlers[0].flush()
    rotated = os.path.exists(str(log_file) + ".1") or os.path.exists(str(log_file) + ".2")
    assert rotated
