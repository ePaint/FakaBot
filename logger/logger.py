import logging
import os
import platform
import sys
from dotenv import load_dotenv

load_dotenv()

# Set styling tags
HEADER = '\033[95m'
TIMESTAMP = '\033[90m'
ORIGIN = '\033[94m'
DEBUG = '\033[96m'
INFO = '\033[92m'
WARNING = '\033[93m'
ERROR = '\033[91m'
BOLD = '\033[1m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'
ENDC = '\033[0m'

# Get logger
logger = logging.getLogger()

# Set labels
timestamp_format = '%Y-%m-%d %H:%M:%S'
timestamp = '[%(asctime)s.%(msecs)03d]'
header_label = '[DRY ]' if os.getenv('DRY_RUN') == 'True' else '[LIVE]'
origin_label = '[%(filename)-18.18s:%(lineno)-4.4d] [%(funcName)-30.30s]'
level_label = '[%(levelname)-4.4s]'


# Create formatters
level = '(LEVEL)'

platform_name = platform.uname().system.lower()
if platform_name == 'linux':
    stream_formatter_template = f'{timestamp} {header_label} {origin_label} {level_label} %(message)s'
else:
    stream_formatter_template = f'{TIMESTAMP}{timestamp}{ENDC} {HEADER}{header_label}{ENDC} {ORIGIN}{origin_label}{ENDC} {level}{level_label}{ENDC} %(message)s'
    # stream_formatter_template = f'{stream_formatter_template} %(name)s'

stream_debug_format = stream_formatter_template.replace(level, DEBUG)
stream_info_format = stream_formatter_template.replace(level, INFO)
stream_warning_format = stream_formatter_template.replace(level, WARNING)
stream_error_format = stream_formatter_template.replace(level, ERROR)

stream_debug_formatter = logging.Formatter(stream_debug_format, datefmt=timestamp_format)
stream_info_formatter = logging.Formatter(stream_info_format, datefmt=timestamp_format)
stream_warning_formatter = logging.Formatter(stream_warning_format, datefmt=timestamp_format)
stream_error_formatter = logging.Formatter(stream_error_format, datefmt=timestamp_format)


# Create handlers
stream_debug_handler = logging.StreamHandler(sys.stdout)
stream_info_handler = logging.StreamHandler(sys.stdout)
stream_warning_handler = logging.StreamHandler(sys.stderr)
stream_error_handler = logging.StreamHandler(sys.stderr)

# Set formatters
stream_debug_handler.setFormatter(stream_debug_formatter)
stream_info_handler.setFormatter(stream_info_formatter)
stream_warning_handler.setFormatter(stream_warning_formatter)
stream_error_handler.setFormatter(stream_error_formatter)

# Set logging levels
stream_debug_handler.setLevel(logging.DEBUG)
stream_info_handler.setLevel(logging.INFO)
stream_warning_handler.setLevel(logging.WARNING)
stream_error_handler.setLevel(logging.ERROR)


# Create filters
class DebugFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG


class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO


class WarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.WARNING


class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.ERROR


# Set filters
stream_debug_handler.addFilter(DebugFilter())
stream_info_handler.addFilter(InfoFilter())
stream_warning_handler.addFilter(WarningFilter())
stream_error_handler.addFilter(ErrorFilter())


# Add handlers to logger
logger.handlers = [
    stream_debug_handler,
    stream_info_handler,
    stream_warning_handler,
    stream_error_handler,
]

# Set logger level
logger.setLevel(logging.DEBUG)
logger.propagate = False

# Loggers to disable
loggers_to_disable = [
    # 'server',
    # 'uvicorn',
    # 'gunicorn',
    # 'httpx',
    # 'requests',
    # 'httpcore.connection',
    # 'httpcore.http11',
    # 'asyncio',
    # 'datadog.api',
    # 'datadog.util',
    # 'datadog.dogstatsd',
    # 'sqlalchemy.engine',
    # 'sqlalchemy.engine.Engine',
    # 'urllib3.connectionpool',
    # 'discord.voice_state',
    # 'discord.player',
    # 'discord.client',
    # 'discord.gateway',
]

for logger_name in loggers_to_disable:
    logging.getLogger(logger_name).disabled = True
    logging.getLogger(logger_name).setLevel(logging.WARNING)


if os.getenv('LOG_FILE') == 'True':
    file_formatter_template = f'{timestamp} {header_label} {origin_label} {level_label} %(message)s'

    file_debug_format = file_formatter_template.replace(level, DEBUG)
    file_info_format = file_formatter_template.replace(level, INFO)
    file_warning_format = file_formatter_template.replace(level, WARNING)
    file_error_format = file_formatter_template.replace(level, ERROR)

    file_debug_formatter = logging.Formatter(file_debug_format, datefmt=timestamp_format)
    file_info_formatter = logging.Formatter(file_info_format, datefmt=timestamp_format)
    file_warning_formatter = logging.Formatter(file_warning_format, datefmt=timestamp_format)
    file_error_formatter = logging.Formatter(file_error_format, datefmt=timestamp_format)

    file_debug_handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')
    file_info_handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')
    file_warning_handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')
    file_error_handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')

    file_debug_handler.setFormatter(file_debug_formatter)
    file_info_handler.setFormatter(file_info_formatter)
    file_warning_handler.setFormatter(file_warning_formatter)
    file_error_handler.setFormatter(file_error_formatter)

    file_debug_handler.setLevel(logging.DEBUG)
    file_info_handler.setLevel(logging.INFO)
    file_warning_handler.setLevel(logging.WARNING)
    file_error_handler.setLevel(logging.ERROR)

    file_debug_handler.addFilter(DebugFilter())
    file_info_handler.addFilter(InfoFilter())
    file_warning_handler.addFilter(WarningFilter())
    file_error_handler.addFilter(ErrorFilter())

    logger.handlers.extend([
        file_debug_handler,
        file_info_handler,
        file_warning_handler,
        file_error_handler,
    ])

logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(logging.DEBUG)
