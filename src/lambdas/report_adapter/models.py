"""
Data models for the report_adapter Lambda.
Single Responsibility: Define and validate input data structures.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReportAdapterRequest:
    """Represents a validated report adapter request from Step Functions."""

    email: str
    s3_file_path: str
    ai_analysis: Dict[str, Any]
    prompt: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.email:
            raise ValueError("email field is required")
        if not isinstance(self.email, str) or not self.email.strip():
            raise ValueError("email must be a non-empty string")
        if not self.s3_file_path:
            raise ValueError("s3_file_path field is required")
        if not isinstance(self.s3_file_path, str) or not self.s3_file_path.strip():
            raise ValueError("s3_file_path must be a non-empty string")
        if self.ai_analysis is None:
            self.ai_analysis = {}


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
