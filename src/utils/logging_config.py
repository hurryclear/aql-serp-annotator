import logging
import sys


def configure_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """unified logging"""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if root_logger.handlers:
        return

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        root_logger.addHandler(fh)

    for noisy in ("elasticsearch", "urllib3", "botocore", "s3transfer", "absl"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
