import logging
import os


class ColoredFormatter(logging.Formatter):
    """Custom formatter adding colors to log messages based on level"""

    # ANSI color codes
    GREY = "\033[90m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD_RED = "\033[1;91m"
    RESET = "\033[0m"

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        # Determine color based on log level
        if record.levelno == logging.INFO:
            color = self.GREEN
        elif record.levelno == logging.WARNING:
            color = self.YELLOW
        elif record.levelno in (logging.ERROR, logging.CRITICAL):
            color = self.RED
        else:
            color = self.GREY

        # Apply color to the levelname only
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logger_object(
    log_file: str = None, log_dir: str = "logs", log_name: str = "real_estate_logger"
) -> logging.Logger:
    logger = logging.getLogger(name=log_name)
    logger.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatter and add it to the handler
    formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    if log_file:
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        elif log_dir and os.path.exists(log_path := f"{log_dir}/{log_file}"):
            os.remove(log_path)

        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
