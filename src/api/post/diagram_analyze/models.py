from dataclasses import dataclass


@dataclass
class AnalyzeRequest:
    """Represents a validated analyze request."""

    diagram: str  # base64 encoded diagram image
    email: str
    prompt: str | None = None

    def __post_init__(self):
        """Validate required fields."""
        if self.diagram is None:
            raise ValueError("diagram field is required")
        if self.email is None:
            raise ValueError("email field is required")
        if not isinstance(self.diagram, str) or not self.diagram.strip():
            raise ValueError("diagram must be a non-empty string")
        if not isinstance(self.email, str) or not self.email.strip():
            raise ValueError("email must be a non-empty string")
        if self.prompt and not isinstance(self.prompt, str):
            raise ValueError("prompt must be a string")


@dataclass
class DiagramMetadata:
    """Represents metadata about a uploaded diagram."""

    s3_key: str
    s3_bucket: str
    email: str | None = None
    prompt: str | None = None

    @property
    def s3_path(self) -> str:
        """Return full S3 path for reference."""
        return f"s3://{self.s3_bucket}/{self.s3_key}"
