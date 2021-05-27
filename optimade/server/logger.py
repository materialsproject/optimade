"""Logging to both file and terminal"""
import logging
import os
from pathlib import Path
import sys


# Instantiate LOGGER
LOGGER = logging.getLogger("optimade")
LOGGER.setLevel(logging.DEBUG)

# Handler
CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
try:
    from optimade.server.config import CONFIG

    CONSOLE_HANDLER.setLevel(CONFIG.log_level.value.upper())

    if CONFIG.debug:
        CONSOLE_HANDLER.setLevel(logging.DEBUG)


except ImportError:
    CONSOLE_HANDLER.setLevel(os.getenv("OPTIMADE_LOG_LEVEL", "INFO").upper())

# Formatter; try to use uvicorn default, otherwise just use built-in default
try:
    from uvicorn.logging import DefaultFormatter

    CONSOLE_FORMATTER = DefaultFormatter("%(levelprefix)s [%(name)s] %(message)s")
    CONSOLE_HANDLER.setFormatter(CONSOLE_FORMATTER)
except ImportError:
    pass


# Add handler to LOGGER
LOGGER.addHandler(CONSOLE_HANDLER)

# Save a file with all messages (DEBUG level)
try:
    from optimade.server.config import CONFIG

    LOGS_DIR = CONFIG.log_dir
except ImportError:
    LOGS_DIR = Path(os.getenv("OPTIMADE_LOG_DIR", "/var/log/optimade/")).resolve()

try:
    LOGS_DIR.mkdir(exist_ok=True)

    # Handlers
    FILE_HANDLER = logging.handlers.RotatingFileHandler(
        LOGS_DIR.joinpath("optimade.log"), maxBytes=1000000, backupCount=5
    )

except OSError:
    LOGGER.warning(
        f"""Log files are not saved.

    This is usually due to not being able to access a specified log folder or write to files
    in the specified log location, i.e., a `PermissionError` has been raised.

    To solve this, either set the OPTIMADE_LOG_DIR environment variable to a location
    you have permission to write to or create the {LOGS_DIR} folder, which is
    the default logging folder, with write permissions for the Unix user running the server.
    """
    )
else:
    FILE_HANDLER.setLevel(logging.DEBUG)

    # Formatter
    FILE_FORMATTER = logging.Formatter(
        "[%(levelname)-8s %(asctime)s %(filename)s:%(lineno)d][%(name)s] %(message)s",
        "%d-%m-%Y %H:%M:%S",
    )
    FILE_HANDLER.setFormatter(FILE_FORMATTER)

    # Add handler to LOGGER
    LOGGER.addHandler(FILE_HANDLER)
