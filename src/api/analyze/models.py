from dataclasses import dataclass
from typing import Optional


@dataclass
class AnalyzeRequest:
    """Represents a validated analyze request."""
    diagram: str  # base64 encoded diagram image
    email: Optional[str] = None
    prompt: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.diagram:
            raise ValueError("diagram field is required")
        if not isinstance(self.diagram, str) or not self.diagram.strip():
            raise ValueError("diagram must be a non-empty string")
        if self.email and not isinstance(self.email, str):
            raise ValueError("email must be a string")
        if self.prompt and not isinstance(self.prompt, str):
            raise ValueError("prompt must be a string")


@dataclass
class DiagramMetadata:
    """Represents metadata about a uploaded diagram."""
    s3_key: str
    s3_bucket: str
    email: Optional[str] = None
    prompt: Optional[str] = None

    @property
    def s3_path(self) -> str:
        """Return full S3 path for reference."""
        return f"s3://{self.s3_bucket}/{self.s3_key}"
