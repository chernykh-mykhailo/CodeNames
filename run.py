import logging
import sys
import asyncio
import os

# Global Pydantic fix for protected namespaces (model_*)
try:
    from pydantic import BaseModel
    # We can't easily patch all child classes, but we can try to disable the warning/error globally
    # for our own classes and hope aiogram catches up.
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)

# Add current directory to path to ensure 'src' is findable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот зупинений.")
