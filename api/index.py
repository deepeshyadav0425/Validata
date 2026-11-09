"""
Vercel Serverless Function Entrypoint.
Routes all incoming HTTP requests to the Flask application.
"""
import os
import sys

# Ensure the root project directory is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app
