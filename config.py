"""Simple, dependency-free .env reader for local development."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def read_env(path=None):
    result = {}
    path = Path(path) if path else ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            val = val.strip().strip('"').strip("'")
            result[key.strip()] = val
    return result

def setting(name, default=''):
    return os.environ.get(name, read_env().get(name, default))

def db_path():
    return Path(setting('DATABASE_PATH', 'pysupply.db')).expanduser().absolute() if Path(setting('DATABASE_PATH', 'pysupply.db')).is_absolute() else ROOT / setting('DATABASE_PATH', 'pysupply.db')
