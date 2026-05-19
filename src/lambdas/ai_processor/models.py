from dataclasses import dataclass


@dataclass
class ProcessImageAIDTO:
    email: str | None
    prompt: str | None
    s3_file_path: str | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            email=data.get("email"),
            prompt=data.get("prompt"),
            s3_file_path=data.get("s3_file_path"),
        )
