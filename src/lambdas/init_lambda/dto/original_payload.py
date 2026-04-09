from dataclasses import dataclass, asdict


@dataclass
class OriginalPayload:
    s3_bucket: str
    s3_key: str
    email: str
    prompt: str

    def to_dict(self) -> dict:
        """
        Converte o objeto OriginalPayload em um dicionário.
        """
        return asdict(self)
