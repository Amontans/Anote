"""Anote 业务逻辑包（src-layout，现代化分层）。"""
from .core import Config, Result, setup_logging
from . import core, services

__all__ = ["Config", "Result", "core", "services", "setup_logging"]
