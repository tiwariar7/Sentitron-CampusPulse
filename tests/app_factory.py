"""
Test-compatible app factory.
Adjusts sys.path so the backend package resolves correctly from the project root,
then imports and returns the FastAPI app.
"""
import os
import sys

# Ensure backend/ is on the path so relative imports like `from services.db` work
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
BACKEND_DIR = os.path.normpath(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Also ensure project root is available
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def create_test_app():
    from api.main import app
    return app
