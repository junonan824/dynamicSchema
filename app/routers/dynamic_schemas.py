from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from .. import crud, database
from ..schemas_dynamic import DynamicSchema, DynamicSchemaCreate, DynamicData, DynamicDataCreate
from ..logger import get_logger
from ..utils.error_handlers import NotFoundError, ValidationFailedError

# 로거 가져오기
logger = get_logger()

router = APIRouter(
    prefix="/dynamic-schemas",
    tags=["dynamic-schemas"],
    responses={
        404: {"description": "스키마를 찾을 수 없습니다"},
        400: {"description": "잘못된 요청 형식입니다"},
        500: {"description": "서버 내부 오류가 발생했습니다"}
    }
)

@router.post("/", response_model=DynamicSchema, 
             summary="새 스키마 생성",
             description="새로운 동적 JSON 스키마를 생성합니다.")
def create_schema(
    request: Request,
    schema: DynamicSchemaCreate = Body(
        ...,
        example={
            "name": "사용자 프로필",
            "description": "사용자 정보를 저장하는 스키마",
            "schema_definition": {
                "name": "사용자 프로필",
                "description": "사용자 정보 스키마",
                "fields": {
                    "이름": {
                        "type": "string",
                        "required": True,
                        "description": "사용자 이름"
                    },
                    "나이": {
                        "type": "integer",
                        "required": True,
                        "description": "사용자 나이"
                    },
                    "이메일": {
                        "type": "string",
                        "required": False,
                        "description": "사용자 이메일"
                    }
                }
            }
        }
    ),
    db: Session = Depends(database.get_db)
):
    """
    새로운 동적 JSON 스키마를 생성합니다.
    
    - **name**: 스키마 이름
    - **description**: 스키마 설명 (선택 사항)
    - **schema_definition**: 스키마 정의 (JSON 형식)
      - **name**: 스키마 이름
      - **description**: 스키마 설명
      - **fields**: 필드 정의 (키-값 쌍)
        - 각 필드는 이름과 정의로 구성
        - 필드 정의에는 type, required, description 등 포함
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        # 스키마 생성
        db_schema = crud.create_dynamic_schema(db=db, schema=schema)
        logger.info(f"Schema created: {db_schema.id}", extra={"request_id": request_id})
        return db_schema
    except ValidationFailedError as e:
        logger.warning(f"Schema validation failed: {str(e)}", extra={"request_id": request_id})
        raise
    except Exception as e:
        logger.error(f"Error creating schema: {str(e)}", extra={"request_id": request_id})
        raise

@router.get("/", response_model=List[DynamicSchema],
            summary="모든 스키마 조회",
            description="등록된 모든 동적 스키마 목록을 조회합니다.")
def read_schemas(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """
    등록된 모든 동적 스키마 목록을 조회합니다.
    
    - **skip**: 건너뛸 레코드 수 (기본값: 0)
    - **limit**: 최대 반환 레코드 수 (기본값: 100)
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        schemas = crud.get_dynamic_schemas(db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(schemas)} schemas", extra={"request_id": request_id})
        return schemas
    except Exception as e:
        logger.error(f"Error retrieving schemas: {str(e)}", extra={"request_id": request_id})
        raise

@router.get("/{schema_id}", response_model=DynamicSchema,
            summary="스키마 상세 조회",
            description="지정된 ID의 스키마 상세 정보를 조회합니다.")
def read_schema(
    request: Request,
    schema_id: int, 
    db: Session = Depends(database.get_db)
):
    """
    지정된 ID의 스키마 상세 정보를 조회합니다.
    
    - **schema_id**: 조회할 스키마의 ID
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        db_schema = crud.get_dynamic_schema(db, schema_id=schema_id)
        if db_schema is None:
            logger.warning(f"Schema not found: {schema_id}", extra={"request_id": request_id})
            raise NotFoundError("Schema", schema_id)
        
        logger.info(f"Retrieved schema: {schema_id}", extra={"request_id": request_id})
        return db_schema
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving schema {schema_id}: {str(e)}", extra={"request_id": request_id})
        raise

@router.put("/{schema_id}", response_model=DynamicSchema,
            summary="스키마 업데이트",
            description="지정된 ID의 스키마를 업데이트합니다.")
def update_schema(
    request: Request,
    schema_id: int, 
    schema: DynamicSchemaCreate = Body(
        ...,
        example={
            "name": "업데이트된 사용자 프로필",
            "description": "사용자 정보를 저장하는 업데이트된 스키마",
            "schema_definition": {
                "name": "업데이트된 사용자 프로필",
                "description": "업데이트된 사용자 정보 스키마",
                "fields": {
                    "이름": {
                        "type": "string",
                        "required": True,
                        "description": "사용자 이름"
                    },
                    "나이": {
                        "type": "integer",
                        "required": True,
                        "description": "사용자 나이"
                    }
                }
            }
        }
    ),
    db: Session = Depends(database.get_db)
):
    """
    지정된 ID의 스키마를 업데이트합니다.
    
    - **schema_id**: 업데이트할 스키마의 ID
    - **schema**: 업데이트할 스키마 정보
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        # 스키마 존재 여부 확인
        db_schema = crud.get_dynamic_schema(db, schema_id=schema_id)
        if db_schema is None:
            logger.warning(f"Schema not found for update: {schema_id}", extra={"request_id": request_id})
            raise NotFoundError("Schema", schema_id)
        
        # 스키마 업데이트
        updated_schema = crud.update_dynamic_schema(db=db, schema_id=schema_id, schema=schema)
        logger.info(f"Updated schema: {schema_id}", extra={"request_id": request_id})
        return updated_schema
    except NotFoundError:
        raise
    except ValidationFailedError as e:
        logger.warning(f"Schema validation failed during update: {str(e)}", extra={"request_id": request_id})
        raise
    except Exception as e:
        logger.error(f"Error updating schema {schema_id}: {str(e)}", extra={"request_id": request_id})
        raise

@router.delete("/{schema_id}", response_model=Dict[str, Any],
               summary="스키마 삭제",
               description="지정된 ID의 스키마를 삭제합니다.")
def delete_schema(
    request: Request,
    schema_id: int, 
    db: Session = Depends(database.get_db)
):
    """
    지정된 ID의 스키마를 삭제합니다.
    
    - **schema_id**: 삭제할 스키마의 ID
    
    **주의**: 스키마를 삭제하면 해당 스키마로 저장된 모든 데이터도 함께 삭제됩니다.
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        # 스키마 존재 여부 확인
        db_schema = crud.get_dynamic_schema(db, schema_id=schema_id)
        if db_schema is None:
            logger.warning(f"Schema not found for deletion: {schema_id}", extra={"request_id": request_id})
            raise NotFoundError("Schema", schema_id)
        
        # 스키마 삭제
        crud.delete_dynamic_schema(db=db, schema_id=schema_id)
        logger.info(f"Deleted schema: {schema_id}", extra={"request_id": request_id})
        return {"success": True, "message": f"Schema {schema_id} deleted successfully"}
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting schema {schema_id}: {str(e)}", extra={"request_id": request_id})
        raise

@router.get("/{schema_id}/validate", response_model=Dict[str, Any],
            summary="스키마 유효성 검증",
            description="지정된 ID의 스키마가 유효한지 검증합니다.")
def validate_schema(
    request: Request,
    schema_id: int, 
    db: Session = Depends(database.get_db)
):
    """
    지정된 ID의 스키마가 유효한지 검증합니다.
    
    - **schema_id**: 검증할 스키마의 ID
    
    **반환값**:
    - **valid**: 스키마 유효성 여부 (boolean)
    - **errors**: 유효하지 않은 경우 오류 메시지 목록
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        # 스키마 존재 여부 확인
        db_schema = crud.get_dynamic_schema(db, schema_id=schema_id)
        if db_schema is None:
            logger.warning(f"Schema not found for validation: {schema_id}", extra={"request_id": request_id})
            raise NotFoundError("Schema", schema_id)
        
        # 스키마 검증
        from ..schemas_dynamic import SchemaDefinition
        try:
            SchemaDefinition(**db_schema.schema_definition)
            logger.info(f"Schema {schema_id} is valid", extra={"request_id": request_id})
            return {"valid": True}
        except Exception as e:
            logger.warning(f"Schema {schema_id} is invalid: {str(e)}", extra={"request_id": request_id})
            return {"valid": False, "errors": str(e)}
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error validating schema {schema_id}: {str(e)}", extra={"request_id": request_id})
        raise

@router.post("/{schema_id}/data", response_model=DynamicData)
def create_data(schema_id: int, data: Dict[str, Any], db: Session = Depends(database.get_db)):
    data_create = DynamicDataCreate(schema_id=schema_id, data=data)
    try:
        return crud.create_dynamic_data(db=db, data_create=data_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{schema_id}/data", response_model=List[DynamicData])
def read_data_by_schema(schema_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_dynamic_data_by_schema(db, schema_id=schema_id, skip=skip, limit=limit) 