"""
Data models for the report_adapter Lambda.
Single Responsibility: Define and validate input data structures.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ReportAdapterRequest:
    """Represents a validated report adapter request from Step Functions."""

    execution_id: str
    email: str
    s3_file_path: str
    prompt: Optional[str] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields."""
        if not self.execution_id:
            raise ValueError("execution_id field is required")
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise ValueError("execution_id must be a non-empty string")
        if not self.email:
            raise ValueError("email field is required")
        if not isinstance(self.email, str) or not self.email.strip():
            raise ValueError("email must be a non-empty string")
        if not self.s3_file_path:
            raise ValueError("s3_file_path field is required")
        if not isinstance(self.s3_file_path, str) or not self.s3_file_path.strip():
            raise ValueError("s3_file_path must be a non-empty string")
        if self.raw_payload is None:
            self.raw_payload = {}
        if not isinstance(self.raw_payload, dict):
            raise ValueError("raw_payload must be a dictionary")


@dataclass
class ReportAdapterResult:
    """Represents the output of the report adapter workflow."""

    status: str
    db_item_id: str
    sqs_message_id: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "status": self.status,
            "db_item_id": self.db_item_id,
            "sqs_message_id": self.sqs_message_id,
        }
