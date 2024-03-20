from typing import Dict, List, Optional
from pydantic import BaseModel


class Error(BaseModel):
    name: str
    value: str
    traceback: List[str]


MIMEType = str


class Result(BaseModel):
    output: Optional[str] = None
    stdout: List[str] = []
    stderr: List[str] = []
    error: Optional[Error] = None
    display_data: List[Dict[MIMEType, str]] = []


class KernelException(Exception):
    """
    Exception raised when a kernel operation fails.
    """

    pass
