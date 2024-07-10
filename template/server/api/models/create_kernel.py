from typing import Any, Dict, Optional
from pydantic import BaseModel, StrictStr
from pydantic import Field


class CreateKernel(BaseModel):
    cwd: Optional[StrictStr] = Field(default=None, description="Current working directory")
    language: Optional[StrictStr] = Field(
        default=None, description="Language of the code to be executed"
    )
    kernel_name: Optional[StrictStr] = Field(default=None, description="Name of the kernel")


class RestartKernel(BaseModel):
    kernel_id: Optional[StrictStr] = Field(default=None, description="Kernel ID")
