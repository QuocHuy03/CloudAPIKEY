import os
from threading import Lock
import pandas as pd
from functools import lru_cache
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database configuration
DATABASE_PATH = os.path.join(BASE_DIR, "keys.db")
USE_SQL_DATABASE = True  # SQL-only mode - CSV files removed

# Output directories
VOICE_OUTPUT_DIR = os.path.join(BASE_DIR, "voices")
IMAGE_OUTPUT_DIR = os.path.join(BASE_DIR, "images")

# API Keys files
GEMINI_KEYS_FILE = os.path.join(BASE_DIR, "gemini_key_tm.txt")
SUDO_KEYS_FILE = os.path.join(BASE_DIR, "suno_key.txt")
EXPIRED_SUDO_KEYS_FILE = os.path.join(BASE_DIR, "expired_keys.txt")
PROXIES_FILE = os.path.join(BASE_DIR, "proxies.txt")

from threading import Lock
csv_lock = Lock()
_csv_cache = {}
_csv_cache_timestamp = {}
CACHE_TTL = 30  # Cache CSV data for 30 seconds

# CSV functionality removed - using SQL database only
# All CSV-related functions have been deprecated
