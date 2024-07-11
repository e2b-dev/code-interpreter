from pydantic import BaseModel, StrictStr
from pydantic import Field


class Context(BaseModel):
    id: StrictStr = Field(description="Context ID")
    name: StrictStr = Field(description="Context name")
