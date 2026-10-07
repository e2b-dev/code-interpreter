"""Minimal httpx client for the E2B control-plane API (sandbox lifecycle only)."""

from dataclasses import dataclass
from typing import Optional

import httpx

CODE_INTERPRETER_PORT = 49999


@dataclass(frozen=True)
class SandboxInfo:
    sandbox_id: str
    domain: str
    envd_access_token: Optional[str]
    traffic_access_token: Optional[str]

    @property
    def code_interpreter_url(self) -> str:
        return f"https://{CODE_INTERPRETER_PORT}-{self.sandbox_id}.{self.domain}"


class SandboxApi:
    def __init__(self, api_key: str, domain: str):
        self.domain = domain
        self._client = httpx.Client(
            base_url=f"https://api.{domain}",
            headers={"X-API-Key": api_key},
            timeout=60,
        )

    def create(
        self,
        template: str,
        *,
        timeout: int,
        metadata: Optional[dict[str, str]] = None,
        envs: Optional[dict[str, str]] = None,
        allow_public_traffic: bool = True,
    ) -> SandboxInfo:
        body: dict = {
            "templateID": template,
            "timeout": timeout,
            "metadata": metadata or {},
            "envVars": envs or {},
        }
        if not allow_public_traffic:
            body["network"] = {"allowPublicTraffic": False}

        response = self._client.post("/v2/sandboxes", json=body)
        response.raise_for_status()
        data = response.json()

        return SandboxInfo(
            sandbox_id=data["sandboxID"],
            domain=data.get("domain") or self.domain,
            envd_access_token=data.get("envdAccessToken"),
            traffic_access_token=data.get("trafficAccessToken"),
        )

    def get(self, sandbox_id: str) -> Optional[dict]:
        response = self._client.get(f"/sandboxes/{sandbox_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def kill(self, sandbox_id: str) -> bool:
        response = self._client.delete(f"/sandboxes/{sandbox_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def close(self) -> None:
        self._client.close()
