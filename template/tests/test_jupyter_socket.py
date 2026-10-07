import asyncio
import os
import socket
import sys
from pathlib import Path

import httpx
from anyio import fail_after

import envs
import messaging
from api.models.output import OutputType
from messaging import ContextWebSocket


async def test_jupyter_http_and_execution_use_unix_socket_only(tmp_path, monkeypatch):
    path = str(tmp_path / "jupyter.sock")
    config = Path(__file__).resolve().parents[1] / "jupyter_server_config.py"
    monkeypatch.setattr(messaging, "JUPYTER_SOCKET_PATH", path)
    monkeypatch.setattr(envs, "LOCAL", True)
    with (tmp_path / "jupyter.log").open("w+") as logs:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "jupyter_server",
            f"--config={config}",
            f"--ServerApp.sock={path}",
            f"--ServerApp.root_dir={tmp_path}",
            "--IdentityProvider.token=",
            stdout=logs,
            stderr=logs,
            env={
                **os.environ,
                "IPYTHONDIR": str(tmp_path / "ipython"),
                "JUPYTER_RUNTIME_DIR": str(tmp_path),
            },
        )
        ws = None
        try:
            async with httpx.AsyncClient(
                transport=httpx.AsyncHTTPTransport(uds=path),
                base_url="http://localhost",
                trust_env=False,
            ) as client:
                with fail_after(30):
                    while True:
                        if process.returncode is not None:
                            logs.seek(0)
                            raise AssertionError(logs.read())
                        try:
                            response = await client.get("/api/status")
                            if response.status_code == 200:
                                break
                        except httpx.RequestError:
                            pass
                        await asyncio.sleep(0.1)

                assert Path(path).stat().st_mode & 0o777 == 0o600
                with socket.socket() as tcp:
                    assert tcp.connect_ex(("127.0.0.1", 8888)) != 0

                response = await client.post("/api/kernels", json={"name": "python3"})
                response.raise_for_status()
                kernel_id = response.json()["id"]
                ws = ContextWebSocket(kernel_id, "session", "python", str(tmp_path))
                await ws.connect()
                with fail_after(30):
                    outputs = [item async for item in ws.execute("6 * 7", {}, None)]
                assert any(
                    item["type"] == OutputType.RESULT and item["text"] == "42"
                    for item in outputs
                ), outputs
                outputs = []
                with fail_after(10):
                    async for item in ws.execute(
                        'print("started", flush=True)\nimport time\ntime.sleep(60)',
                        {},
                        None,
                    ):
                        outputs.append(item)
                        if item["type"] == OutputType.STDOUT:
                            await ws.interrupt()
                assert any(
                    item["type"] == OutputType.ERROR
                    and item["name"] == "KeyboardInterrupt"
                    for item in outputs
                ), outputs
                assert (
                    await client.delete(f"/api/kernels/{kernel_id}")
                ).status_code == 204
        finally:
            if ws is not None:
                await ws.close()
            if process.returncode is None:
                process.terminate()
            await process.wait()
