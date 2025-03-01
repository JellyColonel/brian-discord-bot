# brian-discord-bot/utils/logger.py

import logging
import os
from datetime import datetime

def setup_logger():
    """Set up and configure logger"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logging
    logger = logging.getLogger('discord_bot')
    logger.setLevel(logging.INFO)
    
    # Create a file handler
    log_filename = datetime.now().strftime('logs/bot_%Y-%m-%d_%H-%M-%S.log')
    file_handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_discord_logger():
    """Get Discord.py's logger to capture its messages too"""
    return logging.getLogger('disnake')