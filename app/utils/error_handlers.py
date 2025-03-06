from fastapi import HTTPException, status
from typing import Dict, Any, Optional, Type, List, Union
from pydantic import ValidationError

class APIError(Exception):
    """API 에러 기본 클래스"""
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        code: str = None,
        data: Dict[str, Any] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.code = code
        self.data = data
        super().__init__(detail)

class NotFoundError(APIError):
    """리소스를 찾을 수 없는 경우"""
    def __init__(self, resource_type: str, resource_id: Union[str, int]):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with id {resource_id} not found",
            code="not_found"
        )

class ValidationFailedError(APIError):
    """데이터 검증 실패"""
    def __init__(self, detail: str, errors: List[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code="validation_failed",
            data={"errors": errors} if errors else None
        )

class DuplicateResourceError(APIError):
    """중복된 리소스"""
    def __init__(self, resource_type: str, field: str, value: Any):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource_type} with {field}={value} already exists",
            code="duplicate_resource"
        )

class DatabaseError(APIError):
    """데이터베이스 오류"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            code="database_error"
        )

def handle_validation_error(e: ValidationError) -> Dict[str, Any]:
    """Pydantic ValidationError 처리"""
    errors = []
    for error in e.errors():
        errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    return {
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": "Validation error",
        "code": "validation_error",
        "errors": errors
    }

def handle_api_error(e: APIError) -> Dict[str, Any]:
    """APIError 처리"""
    response = {
        "status_code": e.status_code,
        "detail": e.detail
    }
    
    if e.code:
        response["code"] = e.code
    
    if e.data:
        response["data"] = e.data
    
    return response

def handle_generic_error(e: Exception) -> Dict[str, Any]:
    """일반 예외 처리"""
    return {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": "Internal server error",
        "code": "internal_error"
    } 