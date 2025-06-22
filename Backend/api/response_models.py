from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel
from enum import Enum

T = TypeVar('T')

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class ApiError(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class StandardResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    message: str
    data: Optional[T] = None
    errors: Optional[List[ApiError]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    message: str
    data: List[T]
    pagination: Optional[Dict[str, Any]] = None
    errors: Optional[List[ApiError]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

def create_success_response(data: T, message: str = "Success", warnings: List[str] = None, metadata: Dict[str, Any] = None) -> StandardResponse[T]:
    return StandardResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata
    )

def create_error_response(message: str, errors: List[ApiError] = None, status_code: int = 400) -> StandardResponse[None]:
    return StandardResponse(
        status=ResponseStatus.ERROR,
        message=message,
        errors=errors or [],
        data=None
    )

def create_warning_response(data: T, message: str, warnings: List[str], metadata: Dict[str, Any] = None) -> StandardResponse[T]:
    return StandardResponse(
        status=ResponseStatus.WARNING,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata
    )