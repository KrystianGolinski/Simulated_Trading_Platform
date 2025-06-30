from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field
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

class PaginationInfo(BaseModel):
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, le=1000, description="Number of items per page")
    total_count: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

class PaginatedResponse(BaseModel, Generic[T]):
    status: ResponseStatus
    message: str
    data: List[T]
    pagination: PaginationInfo
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

def create_paginated_response(
    data: List[T], 
    page: int, 
    page_size: int, 
    total_count: int, 
    message: str = "Success",
    warnings: List[str] = None,
    metadata: Dict[str, Any] = None
) -> PaginatedResponse[T]:
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1
    
    pagination_info = PaginationInfo(
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )
    
    return PaginatedResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        pagination=pagination_info,
        warnings=warnings,
        metadata=metadata
    )