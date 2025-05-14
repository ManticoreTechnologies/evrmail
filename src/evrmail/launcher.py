#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import logging
import argparse
import platform
import threading
from pathlib import Path

from . import __version__
from .utils import set_logging_level
from .daemon.daemon import EVRMailDaemon
from .gui.gui import start_gui

# Configure logger
log = logging.getLogger('evrmail.launcher')

def handle_sigint(sig, frame):
    log.info("Received SIGINT, shutting down...")
    sys.exit(0)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='EvrMail Launcher')
    parser.add_argument('--version', action='version', version=f'EvrMail {__version__}')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-gui', action='store_true', help='Run only the daemon, without GUI')
    parser.add_argument('--no-daemon', action='store_true', help='Run only the GUI, without daemon')
    parser.add_argument('--nodejs', action='store_true', help='Run GUI in development mode with NodeJS')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set log level (overrides --debug)')
    return parser.parse_args()

def start_daemon():
    """Start the EVRMailDaemon."""
    log.info("Starting EVRMailDaemon...")
    daemon = EVRMailDaemon()
    daemon_thread = threading.Thread(target=daemon.run)
    daemon_thread.daemon = True
    daemon_thread.start()
    return daemon

def main():
    """Main entry point for EvrMail."""
    # Parse command line arguments
    args = parse_args()
    
    # Setup logging
    if args.log_level:
        set_logging_level(args.log_level)
    elif args.debug:
        set_logging_level('DEBUG')
    else:
        set_logging_level('INFO')
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Log platform information
    log.info(f"Starting EvrMail {__version__} on {platform.platform()}")
    
    # Start daemon
    daemon = None
    if not args.no_daemon:
        try:
            daemon = start_daemon()
            log.info("EVRMailDaemon started successfully")
        except Exception as e:
            log.error(f"Failed to start EVRMailDaemon: {e}")
            if not args.no_gui:
                log.warning("Continuing with GUI only...")
            else:
                log.error("Exiting due to daemon startup failure")
                sys.exit(1)
    
    # Start GUI
    if not args.no_gui:
        try:
            log.info("Starting GUI...")
            # Give the daemon a moment to initialize
            if daemon:
                time.sleep(1)
            
            # Check if we should use nodejs mode
            nodejs_mode = args.nodejs
            log.info(f"Starting GUI with nodejs mode: {nodejs_mode}")
            
            # Start the GUI with the appropriate mode
            start_gui(nodejs=nodejs_mode)
        except Exception as e:
            log.error(f"Failed to start GUI: {e}")
            sys.exit(1)
    else:
        # If only daemon is running, keep main thread alive
        if daemon:
            log.info("Running in daemon-only mode (no GUI)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                log.info("Received KeyboardInterrupt, shutting down...")
        else:
            log.error("No components started (both GUI and daemon disabled)")
            sys.exit(1)

if __name__ == "__main__":
    main() 