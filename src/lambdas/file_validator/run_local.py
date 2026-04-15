import json
import sys
from pathlib import Path

# <repo>/src/lambdas/file_validator/run_local.py
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent.parent
REPO_DIR = SRC_DIR.parent

# Add import paths needed for local execution.
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(1, str(SRC_DIR))
sys.path.insert(2, str(SRC_DIR / "layers" / "common" / "python"))

from handler import lambda_handler


if __name__ == "__main__":
    event = {
        "s3_file_path": "s3://auto-arch-analyzer-diagram-upload-dev/voce/95490a0e-diagram.png",
        "email": "user@example.com",
        "prompt": "Analyze this architecture",
    }

    result = lambda_handler(event, None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
