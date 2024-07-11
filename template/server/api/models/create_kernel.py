from typing import Any, Dict, Optional
from pydantic import BaseModel, StrictStr
from pydantic import Field


class CreateContext(BaseModel):
    cwd: Optional[StrictStr] = Field(
        default=None, description="Current working directory"
    )
    language: Optional[StrictStr] = Field(
        default=None, description="Language of the code to be executed"
    )
    kernel_name: Optional[StrictStr] = Field(
        default=None, description="Name of the kernel"
    )


class RestartContext(BaseModel):
    kernel_id: Optional[StrictStr] = Field(default=None, description="Kernel ID")


class ShutdownKernel(BaseModel):
    kernel_id: Optional[StrictStr] = Field(default=None, description="Kernel ID")
