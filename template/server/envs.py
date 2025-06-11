import os

import httpx

LOCAL = os.getenv("E2B_LOCAL", False)
ENVD_PORT = 49983


async def get_envs() -> dict:
    if LOCAL:
        return {
            "E2B_TEST_VARIABLE": "true"
        }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:{ENVD_PORT}/envs")
        return response.json()
