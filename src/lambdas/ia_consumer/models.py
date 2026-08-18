from dataclasses import dataclass
from typing import Optional


@dataclass
class IAConsumerRequest:
    prompt: str
    imagem_url: Optional[str] = None
    s3_file_path: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        has_imagem_url = isinstance(self.imagem_url, str) and self.imagem_url.strip()
        has_s3_file_path = (
            isinstance(self.s3_file_path, str) and self.s3_file_path.strip()
        )

        if not has_imagem_url and not has_s3_file_path:
            raise ValueError("imagem_url or s3_file_path is required")

        if self.imagem_url is not None and not isinstance(self.imagem_url, str):
            raise ValueError("imagem_url must be a string")

        if self.s3_file_path is not None and not isinstance(self.s3_file_path, str):
            raise ValueError("s3_file_path must be a string")
