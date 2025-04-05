# typer.pyi

from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from types import TracebackType
from pathlib import Path
from enum import Enum
from datetime import datetime
from uuid import UUID

import click

from .core import (
    MarkupMode,
    TyperArgument,
    TyperCommand,
    TyperGroup,
    TyperOption,
)
from .models import (
    CommandFunctionType,
    DeveloperExceptionConfig,
    TyperInfo,
)

class Typer:
    def __init__(
        self,
        *,
        name: Optional[str] = ..., 
        cls: Optional[Type[TyperGroup]] = ..., 
        invoke_without_command: bool = ..., 
        no_args_is_help: bool = ..., 
        subcommand_metavar: Optional[str] = ..., 
        chain: bool = ..., 
        result_callback: Optional[Callable[..., Any]] = ..., 
        context_settings: Optional[Dict[Any, Any]] = ..., 
        callback: Optional[Callable[..., Any]] = ..., 
        help: Optional[str] = ..., 
        epilog: Optional[str] = ..., 
        short_help: Optional[str] = ..., 
        options_metavar: str = ..., 
        add_help_option: bool = ..., 
        hidden: bool = ..., 
        deprecated: bool = ..., 
        add_completion: bool = ..., 
        rich_markup_mode: MarkupMode = ..., 
        rich_help_panel: Optional[str] = ..., 
        pretty_exceptions_enable: bool = ..., 
        pretty_exceptions_show_locals: bool = ..., 
        pretty_exceptions_short: bool = ...,
    ) -> None: ...

    def callback(self, **kwargs: Any) -> Callable[[CommandFunctionType], CommandFunctionType]: ...
    def command(self, name: Optional[str] = ..., **kwargs: Any) -> Callable[[CommandFunctionType], CommandFunctionType]: ...
    def add_typer(self, typer_instance: "Typer", **kwargs: Any) -> None: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

def run(function: Callable[..., Any]) -> None: ...
def launch(url: str, wait: bool = False, locate: bool = False) -> int: ...
def except_hook(exc_type: Type[BaseException], exc_value: BaseException, tb: Optional[TracebackType]) -> None: ...
def get_install_completion_arguments() -> Tuple[click.Parameter, click.Parameter]: ...

def get_command(typer_instance: Typer) -> click.Command: ...
def get_group(typer_instance: Typer) -> TyperGroup: ...
