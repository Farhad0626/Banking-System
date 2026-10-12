from banking.application.context.application_context import ApplicationContext
from banking.infrastructure.bootstrap.composition_root import compose
from banking.infrastructure.configuration.environment_configuration import EnvironmentConfiguration
from banking.infrastructure.logging.logging_config import setup_logging


def create_application() -> ApplicationContext:
    """Entry point for main.py: load settings, configure logging and return a ready-to-run application."""
    config = EnvironmentConfiguration()
    setup_logging(
        level=config.get_str("LOG_LEVEL", "INFO"),
        file_path=config.get_str("LOG_FILE_PATH", "logs/app.log"),
    )
    return compose(config)
