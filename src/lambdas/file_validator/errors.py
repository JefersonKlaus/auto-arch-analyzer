"""
Domain exceptions for file validation workflow.
"""


class FILE_NOT_FOUND(Exception):
    """Raised when the file path points to a non-existing S3 object."""


class INVALID_FORMAT(Exception):
    """Raised when the file is invalid for downstream visual analysis."""
