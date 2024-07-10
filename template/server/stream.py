import json
from typing import Iterable, Mapping, Optional, AsyncIterable, Union

from fastapi.encoders import jsonable_encoder
from starlette.background import BackgroundTask
from fastapi.responses import StreamingResponse


async def async_enumerate(async_sequence: AsyncIterable, start=0):
    """Asynchronously enumerate an async iterator from a given start value.

    See https://stackoverflow.com/a/55930068/9639441
    """
    idx = start
    async for element in async_sequence:
        yield idx, element
        idx += 1


class StreamingLisJsonResponse(StreamingResponse):
    """Converts a pydantic model generator into a streaming HTTP Response
    that streams a JSON list, one element at a time.

    See https://github.com/tiangolo/fastapi/issues/1978
    """

    def __init__(
        self,
        content_generator: Union[Iterable, AsyncIterable],
        status_code: int = 200,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> None:
        if isinstance(content_generator, AsyncIterable):
            body_iterator = self._encoded_async_generator(content_generator)
        else:
            body_iterator = self._encoded_generator(content_generator)
        super().__init__(
            content=body_iterator,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    async def _encoded_async_generator(self, async_generator: AsyncIterable):
        """Converts an asynchronous pydantic model generator
        into a streaming JSON list
        """
        async for idx, item in async_enumerate(async_generator):
            yield json.dumps(jsonable_encoder(item))
            yield "\n"
        yield '{"type": "end_of_execution"}'

    async def _encoded_generator(self, generator):
        """Converts a synchronous pydantic model generator
        into a streaming JSON list
        """
        for idx, item in enumerate(generator):
            yield json.dumps(jsonable_encoder(item))
            yield "\n"
        yield '{"type": "end_of_execution"}'
