"""
Domain models for init-lambda workflow.
Single Responsibility: Define and validate payload data contracts.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InitRequest:
    """Represents a validated init-lambda request payload."""

    s3_bucket: str
    s3_key: str
    email: str
    prompt: Optional[str] = None

    def __post_init__(self):
        """Validate required fields and payload shape."""
        if not isinstance(self.s3_bucket, str) or not self.s3_bucket.strip():
            raise ValueError("s3_bucket must be a non-empty string")
        if not isinstance(self.s3_key, str) or not self.s3_key.strip():
            raise ValueError("s3_key must be a non-empty string")
        if not isinstance(self.email, str) or not self.email.strip():
            raise ValueError("email must be a non-empty string")
        if self.prompt is not None and not isinstance(self.prompt, str):
            raise ValueError("prompt must be a string when provided")

    def to_dict(self) -> dict:
        """Serialize model to dict for Step Functions input."""
        return {
            "s3_bucket": self.s3_bucket,
            "s3_key": self.s3_key,
            "email": self.email,
            "prompt": self.prompt,
        }
