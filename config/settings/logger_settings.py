LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "correlation_id": {"()": "config.settings.log_filters.RequestIDFilter"},
    },
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "[%(correlation_id)s] %(asctime)s  %(name)s  %(levelname)s  %(process)d  %(pathname)s  %(funcName)s  %(lineno)d  "
            "%(message)s  ",
        },
        "rq_console": {
            "format": "%(asctime)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation_id"],
        },
        "rq_console": {
            "level": "DEBUG",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "rq_console",
            "exclude": ["%(asctime)s"],
        },
    },
    "loggers": {
        "core": {
            "handlers": ["console"],
            "filters": ["correlation_id"],
            "level": "INFO",
        },
        "rq.worker": {
            "handlers": [
                "rq_console",
            ],
            "level": "DEBUG",
        },
    },
}
