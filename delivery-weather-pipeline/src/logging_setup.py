import logging
from pathlib import Path


def setup_logging(log_dir: Path):
    # إن لم يكن فولدر السجل موجوداً ننشئه
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("delivery_pipeline")
    # لو الدالة اتنادت مرتين لا نضيف معالجات مكررة
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
