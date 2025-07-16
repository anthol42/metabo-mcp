from dotenv import load_dotenv
from pathlib import Path
import os

def is_claude_key_valid() -> bool:
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    result = os.environ.get("ANTHROPIC_API_KEY") and len(os.environ.get("ANTHROPIC_API_KEY")) > 20 and \
        os.environ.get("ANTHROPIC_API_KEY").startswith("sk-ant-")
    return False if result is None else result

