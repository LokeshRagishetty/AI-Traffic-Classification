import sys
import os

# Ensure the backend root directory is in the Python path
# This allows Vercel to correctly resolve imports like `from models.traffic import ...`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
