"""
📜 EvrMail Logs Command

View, filter, and manage EvrMail log files.
"""

import typer
from .logs import logs_app

__all__ = ["logs_app"] 