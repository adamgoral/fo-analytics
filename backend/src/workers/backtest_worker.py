#!/usr/bin/env python
"""Backtest worker script for processing backtest messages."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from messaging.backtest_consumer import run_backtest_consumer


if __name__ == "__main__":
    print("Starting backtest worker...")
    asyncio.run(run_backtest_consumer())