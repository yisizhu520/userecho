"""
FastAPI Application Entry Point

This module MUST remain minimal to ensure fast startup:
- NO blocking operations at import time
- NO dependency checking (use CLI command instead)
- NO heavy initialization (defer to lifespan)

For plugin dependency management, use:
    python -m backend.cli plugin check-deps
"""
from backend.core.registrar import register_app

# Create FastAPI app instance
# All heavy initialization happens in lifespan (see registrar.py)
app = register_app()
