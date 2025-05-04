import typer
import rich
from rich.console import Console
from rich.table import Table
from rich.text import Text
from pathlib import Path
import re
from datetime import datetime, timedelta
import time
import logging

logs_app = typer.Typer(name="logs", help="Access and filter EvrMail logs")

console = Console()

@logs_app.command("show")
def show_logs(
    category: str = typer.Option("all", "--category", "-c", help="Log category: app, gui, daemon, wallet, chain, net"),
    level: str = typer.Option("info", "--level", "-l", help="Minimum log level: debug, info, warning, error"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs (continuous display)"),
    search: str = typer.Option(None, "--search", "-s", help="Text to search for in logs")
):
    """Display EvrMail logs with filtering options"""
    log_dir = Path.home() / ".evrmail" / "logs"
    
    if not log_dir.exists():
        console.print("[red]Logs directory not found. Run EvrMail first to generate logs.[/red]")
        return
    
    # Determine which log file to read
    if category == "all":
        log_file = log_dir / "evrmail.log"
    else:
        category = category.lower()
        if category == "net":
            category = "network"
        log_file = log_dir / f"evrmail_{category}.log"
    
    if not log_file.exists():
        console.print(f"[red]Log file {log_file} not found.[/red]")
        return
    
    # Level filter
    level_map = {
        "debug": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
        "critical": 4
    }
    min_level = level_map.get(level.lower(), 1)
    
    # Function to parse and filter log lines
    def parse_and_filter(line):
        if not line.strip():
            return None
            
        try:
            # Parse timestamp and level
            match = re.match(r'\[(.*?)\] (\w+): (.*)', line)
            if not match:
                return None
                
            timestamp, level_name, message = match.groups()
            level_num = level_map.get(level_name.lower(), 0)
            
            # Apply level filter
            if level_num < min_level:
                return None
                
            # Apply search filter
            if search and search.lower() not in message.lower():
                return None
                
            # Create colored output
            level_colors = {
                "debug": "dim",
                "info": "white",
                "warning": "yellow",
                "error": "red",
                "critical": "bold red"
            }
            
            color = level_colors.get(level_name.lower(), "white")
            
            # Format the output
            formatted = f"[bright_black][{timestamp}][/bright_black] [{color}]{level_name}:[/{color}] {message}"
            return formatted
            
        except Exception:
            return None
    
    # Display the logs
    if not follow:
        # Just show the last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        filtered_lines = []
        for line in all_lines:
            formatted = parse_and_filter(line)
            if formatted:
                filtered_lines.append(formatted)
        
        # Get the last N filtered lines
        to_display = filtered_lines[-lines:] if lines > 0 else filtered_lines
        
        # Display header
        console.print(f"\n[bold cyan]EvrMail Logs[/bold cyan] - {log_file.name} ({len(to_display)} lines)\n")
        
        # Display logs
        for line in to_display:
            console.print(line)
            
    else:
        # Follow mode - continuously display new logs
        console.print(f"\n[bold cyan]EvrMail Logs[/bold cyan] - {log_file.name} (follow mode) [Press Ctrl+C to exit]\n")
        
        # First show existing logs
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        filtered_lines = []
        for line in all_lines:
            formatted = parse_and_filter(line)
            if formatted:
                filtered_lines.append(formatted)
        
        # Get the last N filtered lines
        to_display = filtered_lines[-lines:] if lines > 0 else filtered_lines
        
        # Display existing logs
        for line in to_display:
            console.print(line)
        
        # Now follow the file
        last_size = log_file.stat().st_size
        
        try:
            while True:
                curr_size = log_file.stat().st_size
                
                if curr_size > last_size:
                    with open(log_file, 'r') as f:
                        f.seek(last_size)
                        new_lines = f.readlines()
                    
                    for line in new_lines:
                        formatted = parse_and_filter(line)
                        if formatted:
                            console.print(formatted)
                    
                    last_size = curr_size
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Log following stopped.[/yellow]")

@logs_app.command("clear")
def clear_logs(
    category: str = typer.Option("all", "--category", "-c", help="Log category: app, gui, daemon, wallet, chain, net, all"),
    confirm: bool = typer.Option(True, "--no-confirm/--confirm", help="Require confirmation before clearing")
):
    """Clear log files"""
    log_dir = Path.home() / ".evrmail" / "logs"
    
    if not log_dir.exists():
        console.print("[red]Logs directory not found. Run EvrMail first to generate logs.[/red]")
        return
    
    # Determine which log files to clear
    files_to_clear = []
    
    if category == "all":
        files_to_clear = list(log_dir.glob("evrmail*.log"))
    else:
        category = category.lower()
        if category == "net":
            category = "network"
        log_file = log_dir / f"evrmail_{category}.log"
        if log_file.exists():
            files_to_clear.append(log_file)
    
    if not files_to_clear:
        console.print(f"[yellow]No log files found for category '{category}'.[/yellow]")
        return
    
    # Confirm before clearing
    if confirm:
        file_list = ", ".join(f.name for f in files_to_clear)
        confirm_clear = typer.confirm(f"Clear these log files? {file_list}")
        if not confirm_clear:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
    
    # Clear the files
    for file in files_to_clear:
        with open(file, 'w') as f:
            pass  # Truncate file
        console.print(f"[green]Cleared log file: {file.name}[/green]")

@logs_app.command("config")
def configure_logging(
    level: str = typer.Option("info", "--level", "-l", help="Default log level: debug, info, warning, error"),
    console_output: bool = typer.Option(True, "--console/--no-console", help="Show logs in console"),
    colored: bool = typer.Option(True, "--colored/--no-color", help="Use colored output"),
    daemon_to_console: bool = typer.Option(False, "--daemon-console/--no-daemon-console", help="Show daemon logs in console")
):
    """Configure logging preferences"""
    from evrmail.utils.logger import (
        configure_logging, set_colored_output, set_daemon_console_output
    )
    
    # Map level string to logging level
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    log_level = level_map.get(level.lower(), logging.INFO)
    
    # Configure logging
    log_dir = configure_logging(
        level=log_level,
        colored=colored,
        daemon_to_console=daemon_to_console
    )
    
    # Set settings
    set_colored_output(colored)
    set_daemon_console_output(daemon_to_console)
    
    # Display confirmation
    console.print(f"[green]Logging configured successfully:[/green]")
    console.print(f"  [cyan]Log directory:[/cyan] {log_dir}")
    console.print(f"  [cyan]Default level:[/cyan] {level.upper()}")
    console.print(f"  [cyan]Console output:[/cyan] {'Enabled' if console_output else 'Disabled'}")
    console.print(f"  [cyan]Colored output:[/cyan] {'Enabled' if colored else 'Disabled'}")
    console.print(f"  [cyan]Daemon to console:[/cyan] {'Enabled' if daemon_to_console else 'Disabled'}")

# Add logrotate functionality
@logs_app.command("rotate")
def rotate_logs():
    """Rotate log files (archive old logs)"""
    log_dir = Path.home() / ".evrmail" / "logs"
    
    if not log_dir.exists():
        console.print("[red]Logs directory not found. Run EvrMail first to generate logs.[/red]")
        return
    
    # Create archives directory
    archives_dir = log_dir / "archives"
    archives_dir.mkdir(exist_ok=True)
    
    # Current timestamp for archive names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Find all log files
    log_files = list(log_dir.glob("evrmail*.log"))
    
    if not log_files:
        console.print("[yellow]No log files found to rotate.[/yellow]")
        return
    
    # Rotate each file
    for log_file in log_files:
        if log_file.stat().st_size == 0:
            continue  # Skip empty files
            
        archive_name = f"{log_file.stem}_{timestamp}.log"
        archive_path = archives_dir / archive_name
        
        # Copy content to archive
        archive_path.write_text(log_file.read_text())
        
        # Clear original file
        with open(log_file, 'w') as f:
            pass  # Truncate file
        
        console.print(f"[green]Rotated {log_file.name} to {archive_name}[/green]")
        
    console.print(f"[green bold]Log rotation complete. Archives saved to {archives_dir}[/green bold]") 