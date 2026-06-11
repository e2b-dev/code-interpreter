import asyncio

import pytest

from e2b import SandboxException
from e2b_code_interpreter import AsyncSandbox


@pytest.mark.skip_debug
async def test_run_code_raises_when_sandbox_is_killed_during_execution(
    async_sandbox: AsyncSandbox,
):
    execution = asyncio.create_task(
        async_sandbox.run_code("import time; time.sleep(60)")
    )

    await asyncio.sleep(2)
    await async_sandbox.kill()

    with pytest.raises(
        SandboxException, match="sandbox was killed while the request was in progress"
    ):
        await execution
