from typing import Optional
from pydantic import BaseModel, StrictStr
from pydantic import Field

from .env_vars import EnvVars


class ExecutionRequest(BaseModel):
    code: StrictStr = Field(description="Code to be executed")
    context_id: Optional[StrictStr] = Field(default="default", description="Context ID")
    env_vars: Optional[EnvVars] = Field(description="Environment variables", default=None)
