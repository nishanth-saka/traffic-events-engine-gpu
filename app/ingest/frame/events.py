import logging

logger = logging.getLogger("events")


def emit_event(event_type: str, **payload):
    logger.info("[EVENT] %s | %s", event_type, payload)
