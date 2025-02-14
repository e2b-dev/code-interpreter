from pydantic import BaseModel, StrictStr, Field
from typing import Optional


class CreateContext(BaseModel):
    cwd: Optional[StrictStr] = Field(
        default="/home/user",
        description="Current working directory",
    )
    language: Optional[StrictStr] = Field(
        default="python", description="Language of the context"
    )
