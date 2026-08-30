"""
Silent launcher for Notion Tasks Desktop Widget.
Running this file with pythonw.exe launches the widget without opening a console window.
"""
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

from desktop_widget import main

if __name__ == "__main__":
    main()
