from dataclasses import dataclass
from typing import Optional


@dataclass
class FileValidationRequest:
    """Represents a validated file validation request."""

    s3_file_path: str
    email: Optional[str] = None
    prompt: Optional[str] = None

    def __post_init__(self):
        """Validate required fields and types."""
        if self.s3_file_path is None:
            raise ValueError("s3_file_path field is required")
        if not isinstance(self.s3_file_path, str) or not self.s3_file_path.strip():
            raise ValueError("s3_file_path must be a non-empty string")
        if self.email is not None and not isinstance(self.email, str):
            raise ValueError("email must be a string")
        if self.prompt is not None and not isinstance(self.prompt, str):
            raise ValueError("prompt must be a string")
