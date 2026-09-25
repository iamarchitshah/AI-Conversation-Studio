"""Root launcher for the AI Conversation Studio API.

Allows `uvicorn main:app` from the repository root while keeping the deployed
application source in outputs/backend.
"""
import importlib.util
import sys
from pathlib import Path

backend_dir = Path(__file__).parent / "outputs" / "backend"
sys.path.insert(0, str(backend_dir))
spec = importlib.util.spec_from_file_location("ai_conversation_backend_main", backend_dir / "main.py")
backend_main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend_main
spec.loader.exec_module(backend_main)
app = backend_main.app
