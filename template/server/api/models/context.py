from pydantic import BaseModel, StrictStr
from pydantic import Field


class Context(BaseModel):
    id: StrictStr = Field(description="Context ID")
    name: StrictStr = Field(description="Context name")
    cwd: StrictStr = Field(description="Current working directory of the context")
