"""Compatibility entry point retained for the repository CI path."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[1]/'generate_answer.py'),run_name='__main__')
