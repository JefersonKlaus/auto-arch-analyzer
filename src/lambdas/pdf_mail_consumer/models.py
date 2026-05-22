"""
Data models for the PDF/Mail consumer.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PdfMailMessage:
    message_id: Optional[str]
    body: Any
    message_attributes: Dict[str, Any]
    event_source: Optional[str]
    event_source_arn: Optional[str]

    @property
    def payload(self) -> Dict[str, Any]:
        if isinstance(self.body, dict):
            return self.body
        return {}

