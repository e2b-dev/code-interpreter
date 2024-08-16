import os

import requests

LOCAL = os.getenv("LOCAL", False)
ENVD_PORT = 49983


def get_envs() -> dict:
    if LOCAL:
        return {}
    return requests.get(f"http://localhost:{ENVD_PORT}/envs").json()
