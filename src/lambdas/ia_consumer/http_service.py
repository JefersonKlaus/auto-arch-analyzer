"""HTTP client for the external IA analysis API."""

import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class IAConsumerApiClient:
    def __init__(self, api_url: str, api_key: str, timeout_seconds: int = 10):
        if not isinstance(api_url, str) or not api_url.strip():
            raise ValueError("IA_CONSUMER_API_URL environment variable not set")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("IA_CONSUMER_API_KEY environment variable not set")

        self.api_url = api_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def analyze(self, prompt: str, imagem_url: str) -> Dict[str, Any]:
        request_body = json.dumps({"prompt": prompt, "imagem_url": imagem_url}).encode(
            "utf-8"
        )
        request = Request(
            self.api_url,
            data=request_body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            },
        )

        try:
            response = urlopen(request, timeout=self.timeout_seconds)
            response_body = response.read().decode("utf-8")
            if not response_body.strip():
                return {}

            try:
                return json.loads(response_body)
            except json.JSONDecodeError:
                return {"raw_response": response_body}

        except HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RuntimeError(
                f"AI consumer API request failed with status {exc.code}: {error_body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"AI consumer API request failed: {exc.reason}") from exc
