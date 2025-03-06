from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from .. import crud, database, models
from ..schemas_dynamic import DynamicData, DynamicDataCreate, SchemaDefinition

router = APIRouter(
    prefix="/dynamic-data",
    tags=["dynamic-data"],
    responses={404: {"description": "Not found"}}
)

@router.post("/validate", response_model=Dict[str, Any])
async def validate_json_data(
    schema_id: int,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """JSON 데이터를 스키마에 따라 검증만 하고 결과 반환"""
    schema = crud.get_dynamic_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema with id {schema_id} not found")
    
    try:
        # 스키마 정의 객체 생성
        schema_def = SchemaDefinition(**schema.schema_definition)
        
        # 데이터 검증
        from ..schemas_dynamic import DynamicDataValidator
        validated_data = DynamicDataValidator.validate_data(schema_def, data)
        
        return {
            "valid": True,
            "validated_data": validated_data
        }
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e)
        }

@router.post("/", response_model=DynamicData)
async def create_dynamic_data_generic(
    data_create: DynamicDataCreate,
    db: Session = Depends(database.get_db)
):
    """스키마 ID와 데이터를 받아 검증 후 저장"""
    try:
        return crud.create_dynamic_data(db, data_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{data_id}", response_model=DynamicData)
async def get_dynamic_data(data_id: int, db: Session = Depends(database.get_db)):
    """저장된 동적 데이터 조회"""
    data = crud.get_dynamic_data(db, data_id)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    return data

@router.get("/", response_model=List[DynamicData])
async def get_all_dynamic_data(
    schema_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """모든 동적 데이터 조회 (선택적으로 스키마 ID로 필터링)"""
    if schema_id:
        return crud.get_dynamic_data_by_schema(db, schema_id, skip, limit)
    
    # 모든 동적 데이터 조회
    return db.query(models.DynamicData).offset(skip).limit(limit).all()

@router.patch("/{data_id}/partial", response_model=DynamicData)
async def partial_update_dynamic_data(
    data_id: int,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    저장된 동적 데이터의 일부만 업데이트 (PATCH)
    기존 데이터를 유지하면서 전달된 필드만 업데이트
    """
    # 기존 데이터 조회
    db_data = crud.get_dynamic_data(db, data_id)
    if not db_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, db_data.schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    try:
        # 스키마 정의 객체 생성
        schema_def = SchemaDefinition(**schema.schema_definition)
        
        # 기존 데이터와 새 데이터 병합
        merged_data = db_data.data.copy()
        merged_data.update(data)
        
        # 병합된 데이터 검증
        from ..schemas_dynamic import DynamicDataValidator
        validated_data = DynamicDataValidator.validate_data(schema_def, merged_data)
        
        # 데이터 업데이트
        db_data.data = validated_data
        db.commit()
        db.refresh(db_data)
        return db_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{data_id}", response_model=DynamicData)
async def update_dynamic_data(
    data_id: int,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    저장된 동적 데이터 전체 업데이트 (PUT)
    기존 데이터를 완전히 대체
    """
    # 기존 데이터 조회
    db_data = crud.get_dynamic_data(db, data_id)
    if not db_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, db_data.schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    try:
        # 스키마 정의 객체 생성
        schema_def = SchemaDefinition(**schema.schema_definition)
        
        # 필수 필드 검증
        for field_name, field_def in schema_def.fields.items():
            if field_def.get('required', False) and field_name not in data:
                raise ValueError(f"Required field '{field_name}' is missing")
        
        # 데이터 검증
        from ..schemas_dynamic import DynamicDataValidator
        validated_data = DynamicDataValidator.validate_data(schema_def, data)
        
        # 데이터 업데이트
        db_data.data = validated_data
        db.commit()
        db.refresh(db_data)
        return db_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{data_id}", response_model=Dict[str, Any])
async def delete_dynamic_data(
    data_id: int, 
    force: bool = False,
    db: Session = Depends(database.get_db)
):
    """
    저장된 동적 데이터 삭제
    
    - force=True: 영구 삭제
    - force=False: 소프트 삭제 (기본값)
    """
    db_data = crud.get_dynamic_data(db, data_id)
    if not db_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    if force:
        # 영구 삭제
        db.delete(db_data)
        db.commit()
        return {"success": True, "message": f"Data with id {data_id} permanently deleted"}
    else:
        # 소프트 삭제 구현 (is_deleted 필드가 있다고 가정)
        # 모델에 is_deleted 필드가 없으면 아래 코드를 주석 처리하고 위의 영구 삭제 코드를 사용
        try:
            # 소프트 삭제 시도
            db_data.is_deleted = True
            db.commit()
            return {"success": True, "message": f"Data with id {data_id} soft deleted"}
        except Exception:
            # is_deleted 필드가 없으면 영구 삭제로 폴백
            db.delete(db_data)
            db.commit()
            return {"success": True, "message": f"Data with id {data_id} permanently deleted (fallback)"}

@router.post("/{data_id}/validate", response_model=Dict[str, Any])
async def validate_data_update(
    data_id: int,
    data: Dict[str, Any] = Body(...),
    partial: bool = False,
    db: Session = Depends(database.get_db)
):
    """
    데이터 업데이트 전에 검증만 수행
    
    - partial=True: 부분 업데이트 검증 (PATCH)
    - partial=False: 전체 업데이트 검증 (PUT)
    """
    # 기존 데이터 조회
    db_data = crud.get_dynamic_data(db, data_id)
    if not db_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    # 스키마 조회
    schema = crud.get_dynamic_schema(db, db_data.schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    try:
        # 스키마 정의 객체 생성
        schema_def = SchemaDefinition(**schema.schema_definition)
        
        # 검증할 데이터 준비
        validate_data = data
        if partial:
            # 부분 업데이트인 경우 기존 데이터와 병합
            validate_data = db_data.data.copy()
            validate_data.update(data)
        else:
            # 전체 업데이트인 경우 필수 필드 검증
            for field_name, field_def in schema_def.fields.items():
                if field_def.get('required', False) and field_name not in data:
                    raise ValueError(f"Required field '{field_name}' is missing")
        
        # 데이터 검증
        from ..schemas_dynamic import DynamicDataValidator
        validated_data = DynamicDataValidator.validate_data(schema_def, validate_data)
        
        # 검증 결과 반환
        return {
            "valid": True,
            "validated_data": validated_data,
            "message": "Data is valid for update"
        }
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Data validation failed"
        }

@router.post("/bulk-delete", response_model=Dict[str, Any])
async def bulk_delete_dynamic_data(
    ids: List[int] = Body(..., embed=True),
    force: bool = False,
    db: Session = Depends(database.get_db)
):
    """여러 데이터를 한 번에 삭제"""
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")
    
    deleted_count = 0
    not_found = []
    
    for data_id in ids:
        db_data = crud.get_dynamic_data(db, data_id)
        if not db_data:
            not_found.append(data_id)
            continue
        
        if force:
            # 영구 삭제
            db.delete(db_data)
        else:
            try:
                # 소프트 삭제 시도
                db_data.is_deleted = True
            except Exception:
                # is_deleted 필드가 없으면 영구 삭제로 폴백
                db.delete(db_data)
        
        deleted_count += 1
    
    # 변경사항 커밋
    db.commit()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "not_found": not_found,
        "delete_type": "permanent" if force else "soft"
    }

@router.post("/bulk-update", response_model=Dict[str, Any])
async def bulk_update_dynamic_data(
    updates: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    여러 데이터를 한 번에 업데이트
    
    updates 형식:
    [
        {"id": 1, "data": {"이름": "홍길동", "나이": 30}},
        {"id": 2, "data": {"이름": "김철수", "나이": 25}}
    ]
    """
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    results = {
        "success": [],
        "failed": []
    }
    
    for update in updates:
        if "id" not in update or "data" not in update:
            results["failed"].append({
                "id": update.get("id", "unknown"),
                "error": "Missing 'id' or 'data' field"
            })
            continue
        
        data_id = update["id"]
        data = update["data"]
        
        # 기존 데이터 조회
        db_data = crud.get_dynamic_data(db, data_id)
        if not db_data:
            results["failed"].append({
                "id": data_id,
                "error": "Data not found"
            })
            continue
        
        # 스키마 조회
        schema = crud.get_dynamic_schema(db, db_data.schema_id)
        if not schema:
            results["failed"].append({
                "id": data_id,
                "error": "Schema not found"
            })
            continue
        
        try:
            # 스키마 정의 객체 생성
            schema_def = SchemaDefinition(**schema.schema_definition)
            
            # 데이터 검증
            from ..schemas_dynamic import DynamicDataValidator
            validated_data = DynamicDataValidator.validate_data(schema_def, data)
            
            # 데이터 업데이트
            db_data.data = validated_data
            results["success"].append({
                "id": data_id,
                "message": "Updated successfully"
            })
        except ValueError as e:
            results["failed"].append({
                "id": data_id,
                "error": str(e)
            })
    
    # 변경사항 커밋
    db.commit()
    
    return results

@router.post("/search", response_model=List[DynamicData])
async def search_dynamic_data(
    search_criteria: Dict[str, Any] = Body(...),
    schema_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """
    동적 데이터를 검색 조건에 따라 조회
    
    search_criteria 예시:
    {
        "field_path": "이름",
        "operator": "eq",
        "value": "홍길동"
    }
    
    또는 복합 조건:
    {
        "and": [
            {"field_path": "나이", "operator": "gt", "value": 20},
            {"field_path": "나이", "operator": "lt", "value": 30}
        ]
    }
    
    또는:
    {
        "or": [
            {"field_path": "이름", "operator": "eq", "value": "홍길동"},
            {"field_path": "이름", "operator": "eq", "value": "김철수"}
        ]
    }
    
    지원하는 연산자:
    - eq: 같음
    - ne: 같지 않음
    - gt: 초과
    - gte: 이상
    - lt: 미만
    - lte: 이하
    - contains: 포함
    - startswith: 시작
    - endswith: 끝남
    """
    
    # 기본 쿼리 생성
    query = db.query(models.DynamicData)
    
    # 스키마 ID로 필터링
    if schema_id:
        query = query.filter(models.DynamicData.schema_id == schema_id)
    
    # 검색 조건 적용
    query = apply_search_criteria(query, search_criteria)
    
    # 결과 반환
    return query.offset(skip).limit(limit).all()

def apply_search_criteria(query, criteria):
    """검색 조건을 쿼리에 적용"""
    
    # 복합 조건 (AND)
    if "and" in criteria:
        for sub_criteria in criteria["and"]:
            query = apply_search_criteria(query, sub_criteria)
        return query
    
    # 복합 조건 (OR)
    if "or" in criteria:
        from sqlalchemy import or_
        conditions = []
        for sub_criteria in criteria["or"]:
            # 각 OR 조건에 대한 서브쿼리 생성
            sub_query = db.query(models.DynamicData.id)
            sub_query = apply_search_criteria(sub_query, sub_criteria)
            conditions.append(models.DynamicData.id.in_(sub_query))
        return query.filter(or_(*conditions))
    
    # 단일 조건
    if all(k in criteria for k in ["field_path", "operator", "value"]):
        field_path = criteria["field_path"]
        operator = criteria["operator"]
        value = criteria["value"]
        
        # JSON 필드 경로 생성
        from sqlalchemy.sql.expression import cast
        from sqlalchemy import String, Integer, Float, Boolean
        
        # 필드 경로에 따른 JSON 추출 표현식
        json_field = models.DynamicData.data[field_path]
        
        # 값 타입에 따른 캐스팅
        if isinstance(value, int):
            json_field = cast(json_field, Integer)
        elif isinstance(value, float):
            json_field = cast(json_field, Float)
        elif isinstance(value, bool):
            json_field = cast(json_field, Boolean)
        else:
            json_field = cast(json_field, String)
        
        # 연산자에 따른 필터 적용
        if operator == "eq":
            return query.filter(json_field == value)
        elif operator == "ne":
            return query.filter(json_field != value)
        elif operator == "gt":
            return query.filter(json_field > value)
        elif operator == "gte":
            return query.filter(json_field >= value)
        elif operator == "lt":
            return query.filter(json_field < value)
        elif operator == "lte":
            return query.filter(json_field <= value)
        elif operator == "contains":
            return query.filter(json_field.contains(value))
        elif operator == "startswith":
            return query.filter(json_field.startswith(value))
        elif operator == "endswith":
            return query.filter(json_field.endswith(value))
    
    return query

@router.post("/advanced-search", response_model=Dict[str, Any])
async def advanced_search_dynamic_data(
    search_params: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db)
):
    """
    고급 검색 기능을 제공하는 엔드포인트
    
    search_params 예시:
    {
        "schema_id": 1,                 # 선택적 스키마 ID
        "conditions": {                 # 검색 조건
            "and": [
                {"field_path": "나이", "operator": "gt", "value": 20},
                {"field_path": "이름", "operator": "contains", "value": "홍"}
            ]
        },
        "sort": [                       # 정렬 조건 (선택적)
            {"field": "나이", "order": "desc"},
            {"field": "이름", "order": "asc"}
        ],
        "pagination": {                 # 페이지네이션 (선택적)
            "page": 1,
            "page_size": 10
        },
        "fields": ["이름", "나이"]      # 반환할 필드 (선택적)
    }
    """
    
    # 기본 쿼리 생성
    query = db.query(models.DynamicData)
    
    # 스키마 ID로 필터링
    if "schema_id" in search_params:
        query = query.filter(models.DynamicData.schema_id == search_params["schema_id"])
    
    # 검색 조건 적용
    if "conditions" in search_params:
        query = apply_search_criteria(query, search_params["conditions"])
    
    # 정렬 적용
    if "sort" in search_params:
        for sort_item in search_params["sort"]:
            field = sort_item["field"]
            order = sort_item.get("order", "asc")
            
            # JSON 필드 경로에 따른 정렬
            from sqlalchemy.sql.expression import cast
            from sqlalchemy import String, desc
            
            json_field = cast(models.DynamicData.data[field], String)
            
            if order.lower() == "desc":
                query = query.order_by(desc(json_field))
            else:
                query = query.order_by(json_field)
    
    # 총 결과 수 계산
    total_count = query.count()
    
    # 페이지네이션 적용
    if "pagination" in search_params:
        page = search_params["pagination"].get("page", 1)
        page_size = search_params["pagination"].get("page_size", 10)
        
        query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 결과 조회
    results = query.all()
    
    # 필드 필터링
    filtered_results = []
    if "fields" in search_params and search_params["fields"]:
        for item in results:
            filtered_data = {}
            for field in search_params["fields"]:
                if field in item.data:
                    filtered_data[field] = item.data[field]
            
            # 원본 데이터 대신 필터링된 데이터 사용
            filtered_item = {
                "id": item.id,
                "schema_id": item.schema_id,
                "data": filtered_data,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            }
            filtered_results.append(filtered_item)
    else:
        filtered_results = [item for item in results]
    
    # 응답 구성
    response = {
        "total": total_count,
        "items": filtered_results
    }
    
    # 페이지네이션 정보 추가
    if "pagination" in search_params:
        page = search_params["pagination"].get("page", 1)
        page_size = search_params["pagination"].get("page_size", 10)
        
        response["pagination"] = {
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    return response

@router.get("/nested-field/{field_path}")
async def get_data_by_nested_field(
    field_path: str,
    value: str,
    schema_id: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """
    중첩된 JSON 필드 경로로 데이터 조회
    
    예: /nested-field/user.address.city?value=서울&schema_id=1
    """
    # 필드 경로를 점(.) 기준으로 분리
    path_parts = field_path.split('.')
    
    # 기본 쿼리 생성
    query = db.query(models.DynamicData)
    
    # 스키마 ID로 필터링
    if schema_id:
        query = query.filter(models.DynamicData.schema_id == schema_id)
    
    # SQLAlchemy JSON 경로 표현식 생성
    from sqlalchemy.sql.expression import cast
    from sqlalchemy import String
    
    # 중첩 경로 처리
    json_path = models.DynamicData.data
    for part in path_parts:
        json_path = json_path[part]
    
    # 문자열로 캐스팅하여 비교
    json_path = cast(json_path, String)
    
    # 필터 적용
    query = query.filter(json_path == value)
    
    # 결과 반환
    results = query.all()
    return results

@router.post("/{data_id}/restore", response_model=DynamicData)
async def restore_dynamic_data(
    data_id: int,
    db: Session = Depends(database.get_db)
):
    """소프트 삭제된 데이터 복원"""
    db_data = crud.restore_dynamic_data(db, data_id)
    if not db_data:
        raise HTTPException(status_code=404, detail="Data not found or not deleted")
    return db_data

@router.get("/deleted", response_model=List[DynamicData])
async def get_deleted_data(
    schema_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """소프트 삭제된 데이터 조회"""
    query = db.query(models.DynamicData)
    
    # is_deleted 필드가 있는 경우에만 필터링
    if hasattr(models.DynamicData, 'is_deleted'):
        query = query.filter(models.DynamicData.is_deleted == True)
    else:
        # is_deleted 필드가 없으면 빈 결과 반환
        return []
    
    # 스키마 ID로 필터링
    if schema_id:
        query = query.filter(models.DynamicData.schema_id == schema_id)
    
    return query.offset(skip).limit(limit).all() 