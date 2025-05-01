from pydantic import BaseModel, StrictStr
from pydantic import Field
from typing import Optional


class CreateContext(BaseModel):
    user: Optional[StrictStr] = Field(
        default="root",
        description="User to run the context",
    )
    cwd: Optional[StrictStr] = Field(
        default="/home/user",
        description="Current working directory",
    )
    language: Optional[StrictStr] = Field(
        default="python", description="Language of the context"
    )
