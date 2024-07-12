from typing import Optional
from pydantic import BaseModel, StrictStr
from pydantic import Field


class ExecutionRequest(BaseModel):
    code: StrictStr = Field(description="Code to be executed")
    context_id: Optional[StrictStr] = Field(default="default", description="Context ID")
