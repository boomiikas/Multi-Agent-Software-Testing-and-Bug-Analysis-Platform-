from typing import Optional, List
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    errors: Optional[List[str]] = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
