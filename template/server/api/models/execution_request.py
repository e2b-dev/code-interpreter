from typing import Any, Dict, Optional
from pydantic import BaseModel, StrictStr
from pydantic import Field


class ExecutionRequest(BaseModel):
    code: StrictStr = Field(description="Code to be executed")
    language: Optional[StrictStr] = Field(
        default=None, description="Language of the code to be executed"
    )
    additional_properties: Dict[str, Any] = {}
