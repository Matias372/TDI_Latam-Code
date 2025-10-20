import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
CONFIG_DIR = os.path.join(DATA_DIR, "config")

# Asegurar que las carpetas existan
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "freshdesk_config.json")
AGENTES_TEMPLATE = os.path.join(TEMPLATES_DIR, "AGENTES_FD.xlsx")