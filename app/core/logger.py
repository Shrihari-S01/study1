"""
Application logging configuration.
"""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import get_settings


# ==========================================================
# Settings
# ==========================================================

settings = get_settings()

LOG_DIR = settings.log_dir

LOG_FILE = LOG_DIR / "auction_ai.log"


# ==========================================================
# Logger Configuration
# ==========================================================

def configure_logging() -> None:
    """
    Configure application logging.
    """

    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(settings.log_level)

    formatter = logging.Formatter(

        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),

        datefmt="%Y-%m-%d %H:%M:%S",

    )

    # ======================================================
    # Console Handler
    # ======================================================

    console_handler = logging.StreamHandler()

    console_handler.setLevel(settings.log_level)

    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # ======================================================
    # File Handler
    # ======================================================

    file_handler = TimedRotatingFileHandler(

        filename=LOG_FILE,

        when="midnight",

        interval=1,

        backupCount=30,

        encoding="utf-8",

    )

    file_handler.setLevel(settings.log_level)

    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)


# ==========================================================
# Logger Factory
# ==========================================================

def get_logger(
    name: str,
) -> logging.Logger:
    """
    Return configured logger.

    Parameters
    ----------
    name : str
        Module name.

    Returns
    -------
    logging.Logger
    """

    configure_logging()

    return logging.getLogger(name)


class PipelineStageTimer:
    """
    Lightweight stage profiler that tracks execution durations per pipeline sub-stage
    and logs a formatted Pipeline Performance Report highlighting the primary bottleneck.
    """

    def __init__(self) -> None:
        import time
        self.start_time = time.time()
        self.stage_durations: dict[str, float] = {}

    def record_stage(self, stage_name: str, duration_seconds: float) -> None:
        self.stage_durations[stage_name] = round(duration_seconds, 3)

    def generate_report(self, logger_instance: logging.Logger = None) -> dict:
        import time
        total_time = round(time.time() - self.start_time, 2)
        log = logger_instance or logging.getLogger(__name__)

        report_lines = ["\n==================================================", "Pipeline Performance Report", ""]
        primary_bottleneck = "None"
        max_duration = 0.0

        for stage, duration in self.stage_durations.items():
            pct = (duration / total_time * 100.0) if total_time > 0 else 0.0
            report_lines.append(f"{stage:<24} : {duration:6.2f} s ({pct:4.1f}%)")
            if duration > max_duration:
                max_duration = duration
                primary_bottleneck = f"{stage} ({pct:.1f}%)"

        report_lines.append("")
        report_lines.append(f"Total Time               : {total_time:6.2f} s")
        report_lines.append(f"Bottleneck               : {primary_bottleneck}")
        report_lines.append("==================================================\n")

        log.info("\n".join(report_lines))
        return {
            "total_time": total_time,
            "durations": self.stage_durations,
            "primary_bottleneck": primary_bottleneck,
        }