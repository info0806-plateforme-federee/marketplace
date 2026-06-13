"""Configuration de la journalisation.

Configure `structlog` pour que toute l'application émette des lignes de log JSON
structurées sur stdout (un objet par ligne), ce qui est pratique pour les
collecteurs de logs de conteneurs. Appeler `setup_logging()` une seule fois au
démarrage du processus avant de créer des loggers.
"""

import logging
import sys

import structlog


def setup_logging() -> None:
    """Configure structlog + la journalisation standard pour une sortie JSON sur stdout.

    Achemine le logger racine de la bibliothèque standard via un formateur JSON
    structlog, fixe le niveau à INFO et fait taire le logger d'accès d'uvicorn.
    Modifie l'état global de journalisation et doit être appelée exactement une fois
    au démarrage.

    Retourne :
        None.
    """

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
    )

    root_logger.handlers = [handler]

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
