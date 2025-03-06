from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import SQLAlchemyError

from .. import crud, database, models
from ..schemas_dynamic import DynamicSchema, SchemaDefinition
from ..utils.error_handlers import NotFoundError, ValidationFailedError, DatabaseError
from ..logger import get_logger

# 로거 가져오기
logger = get_logger()

router = APIRouter(
    prefix="/schema-fields",
    tags=["schema-fields"],
    responses={404: {"description": "Not found"}}
)

@router.post("/{schema_id}/fields", response_model=DynamicSchema)
async def add_field_to_schema(
    request: Request,
    schema_id: int,
    field_definition: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    스키마에 새 필드 추가
    
    field_definition 예시:
    {
        "name": "이메일",
        "definition": {
            "type": "string",
            "required": false,
            "description": "사용자 이메일"
        }
    }
    """
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    try:
        # 스키마 조회
        schema = crud.get_dynamic_schema(db, schema_id)
        if not schema:
            logger.warning(f"Schema with id {schema_id} not found", extra={"request_id": request_id})
            raise NotFoundError("Schema", schema_id)
        
        # 필드 이름과 정의 추출
        if "name" not in field_definition or "definition" not in field_definition:
            logger.warning(
                "Invalid field definition: missing name or definition", 
                extra={"request_id": request_id}
            )
            raise ValidationFailedError("Field definition must include 'name' and 'definition'")
        
        field_name = field_definition["name"]
        field_def = field_definition["definition"]
        
        # 스키마 정의 가져오기
        schema_definition = schema.schema_definition
        
        # 필드가 이미 존재하는지 확인
        if "fields" in schema_definition and field_name in schema_definition["fields"]:
            logger.warning(
                f"Field '{field_name}' already exists in schema {schema_id}", 
                extra={"request_id": request_id}
            )
            raise ValidationFailedError(f"Field '{field_name}' already exists")
        
        # 필드 추가
        if "fields" not in schema_definition:
            schema_definition["fields"] = {}
        
        schema_definition["fields"][field_name] = field_def
        
        # 스키마 정의 검증
        try:
            # 스키마 정의 객체 생성 및 검증
            SchemaDefinition(**schema_definition)
        except ValueError as e:
            logger.warning(
                f"Invalid field definition: {str(e)}", 
                extra={"request_id": request_id}
            )
            raise ValidationFailedError(f"Invalid field definition: {str(e)}")
        
        # 스키마 업데이트
        try:
            schema.schema_definition = schema_definition
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                f"Database error while updating schema: {str(e)}", 
                extra={"request_id": request_id}
            )
            raise DatabaseError("Failed to update schema")
        
        logger.info(
            f"Field '{field_name}' added to schema {schema_id}", 
            extra={"request_id": request_id}
        )
        return schema
    
    except (NotFoundError, ValidationFailedError, DatabaseError):
        # 이미 처리된 예외는 다시 발생시켜 전역 핸들러로 전달
        raise
    except Exception as e:
        # 예상치 못한 예외 로깅
        logger.error(
            f"Unexpected error in add_field_to_schema: {str(e)}", 
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise

@router.put("/{schema_id}/fields/{field_name}", response_model=DynamicSchema)
async def update_field_in_schema(
    schema_id: int,
    field_name: str,
    field_definition: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    스키마의 기존 필드 업데이트
    
    field_definition 예시:
    {
        "type": "string",
        "required": true,
        "description": "사용자 이메일 (필수)"
    }
    """
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # 스키마 정의 가져오기
    schema_definition = schema.schema_definition
    
    # 필드가 존재하는지 확인
    if "fields" not in schema_definition or field_name not in schema_definition["fields"]:
        raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found")
    
    # 필드 업데이트
    schema_definition["fields"][field_name] = field_definition
    
    # 스키마 정의 검증
    try:
        # 스키마 정의 객체 생성 및 검증
        SchemaDefinition(**schema_definition)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid field definition: {str(e)}")
    
    # 스키마 업데이트
    schema.schema_definition = schema_definition
    db.commit()
    
    return schema

@router.delete("/{schema_id}/fields/{field_name}", response_model=DynamicSchema)
async def delete_field_from_schema(
    schema_id: int,
    field_name: str,
    db: Session = Depends(database.get_db)
):
    """스키마에서 필드 삭제"""
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # 스키마 정의 가져오기
    schema_definition = schema.schema_definition
    
    # 필드가 존재하는지 확인
    if "fields" not in schema_definition or field_name not in schema_definition["fields"]:
        raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found")
    
    # 필드 삭제
    del schema_definition["fields"][field_name]
    
    # 스키마 정의 검증
    try:
        # 스키마 정의 객체 생성 및 검증
        SchemaDefinition(**schema_definition)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid schema after field removal: {str(e)}")
    
    # 스키마 업데이트
    schema.schema_definition = schema_definition
    db.commit()
    
    return schema

@router.post("/{schema_id}/fields/validate", response_model=Dict[str, Any])
async def validate_field_definition(
    schema_id: int,
    field_definition: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    필드 정의 검증 (스키마에 추가하지 않고 검증만 수행)
    
    field_definition 예시:
    {
        "name": "이메일",
        "definition": {
            "type": "string",
            "required": false,
            "description": "사용자 이메일"
        }
    }
    """
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # 필드 이름과 정의 추출
    if "name" not in field_definition or "definition" not in field_definition:
        return {
            "valid": False,
            "error": "Field definition must include 'name' and 'definition'"
        }
    
    field_name = field_definition["name"]
    field_def = field_definition["definition"]
    
    # 스키마 정의 복사
    schema_definition = schema.schema_definition.copy()
    
    # 필드 추가
    if "fields" not in schema_definition:
        schema_definition["fields"] = {}
    
    schema_definition["fields"][field_name] = field_def
    
    # 스키마 정의 검증
    try:
        # 스키마 정의 객체 생성 및 검증
        SchemaDefinition(**schema_definition)
        return {
            "valid": True,
            "message": "Field definition is valid"
        }
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e)
        }

@router.post("/{schema_id}/migrate-data", response_model=Dict[str, Any])
async def migrate_existing_data(
    schema_id: int,
    migration_config: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    스키마 변경 후 기존 데이터 마이그레이션
    
    migration_config 예시:
    {
        "field_mappings": {
            "old_field_name": "new_field_name"
        },
        "default_values": {
            "new_required_field": "기본값"
        },
        "remove_fields": ["field_to_remove"]
    }
    """
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # 스키마에 해당하는 모든 데이터 조회
    data_items = crud.get_dynamic_data_by_schema(db, schema_id, include_deleted=True)
    
    # 마이그레이션 설정
    field_mappings = migration_config.get("field_mappings", {})
    default_values = migration_config.get("default_values", {})
    remove_fields = migration_config.get("remove_fields", [])
    
    # 스키마 정의 객체 생성
    schema_def = SchemaDefinition(**schema.schema_definition)
    
    # 마이그레이션 결과 추적
    results = {
        "total": len(data_items),
        "migrated": 0,
        "failed": 0,
        "errors": []
    }
    
    # 각 데이터 항목 마이그레이션
    for item in data_items:
        try:
            # 데이터 복사
            migrated_data = item.data.copy()
            
            # 필드 매핑 적용
            for old_field, new_field in field_mappings.items():
                if old_field in migrated_data:
                    migrated_data[new_field] = migrated_data[old_field]
                    if old_field != new_field:  # 이름이 변경된 경우에만 삭제
                        del migrated_data[old_field]
            
            # 기본값 적용
            for field, value in default_values.items():
                if field not in migrated_data:
                    migrated_data[field] = value
            
            # 필드 제거
            for field in remove_fields:
                if field in migrated_data:
                    del migrated_data[field]
            
            # 데이터 검증
            from ..schemas_dynamic import DynamicDataValidator
            validated_data = DynamicDataValidator.validate_data(schema_def, migrated_data)
            
            # 데이터 업데이트
            item.data = validated_data
            results["migrated"] += 1
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "id": item.id,
                "error": str(e)
            })
    
    # 변경사항 커밋
    db.commit()
    
    return results

@router.get("/{schema_id}/fields", response_model=Dict[str, Any])
async def get_schema_fields(
    schema_id: int,
    db: Session = Depends(database.get_db)
):
    """스키마의 모든 필드 조회"""
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # 스키마 정의 가져오기
    schema_definition = schema.schema_definition
    
    # 필드 반환
    fields = schema_definition.get("fields", {})
    
    return {
        "schema_id": schema_id,
        "schema_name": schema.name,
        "fields": fields
    }

@router.post("/{schema_id}/bulk-add-fields", response_model=DynamicSchema)
async def bulk_add_fields_to_schema(
    schema_id: int,
    fields: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    스키마에 여러 필드 한 번에 추가
    
    fields 예시:
    [
        {
            "name": "이메일",
            "definition": {
                "type": "string",
                "required": false
            }
        },
        {
            "name": "전화번호",
            "definition": {
                "type": "string",
                "required": false
            }
        }
    ]
    """
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # 스키마 정의 가져오기
    schema_definition = schema.schema_definition
    
    # 필드 컨테이너 확인
    if "fields" not in schema_definition:
        schema_definition["fields"] = {}
    
    # 필드 추가
    for field in fields:
        if "name" not in field or "definition" not in field:
            raise HTTPException(status_code=400, detail="Each field must include 'name' and 'definition'")
        
        field_name = field["name"]
        field_def = field["definition"]
        
        # 필드 추가
        schema_definition["fields"][field_name] = field_def
    
    # 스키마 정의 검증
    try:
        # 스키마 정의 객체 생성 및 검증
        SchemaDefinition(**schema_definition)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid field definition: {str(e)}")
    
    # 스키마 업데이트
    schema.schema_definition = schema_definition
    db.commit()
    
    return schema 