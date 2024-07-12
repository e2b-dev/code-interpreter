from pydantic import BaseModel, StrictStr
from pydantic import Field
from typing import Optional


class CreateContext(BaseModel):
    cwd: Optional[StrictStr] = Field(
        default="/home/user",
        description="Current working directory",
    )
    name: Optional[StrictStr] = Field(
        default="python", description="Name of the kernel"
    )
