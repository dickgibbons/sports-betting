# DataGolf API Configuration
# Replace with your actual API key
DATAGOLF_API_KEY = "4ab9cd9340bb9a48b57ec6ffece9"

# Base URL for DataGolf API
DATAGOLF_BASE_URL = "https://feeds.datagolf.com"

# Data directories
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
