# app/shared.py

# Shared application state to avoid circular imports
from app.state import app_state

# Export app_state for shared usage
__all__ = ["app_state"]