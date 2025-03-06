from sqlalchemy.orm import Session
from . import models, schemas
from . import schemas_dynamic

def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, item: schemas.ItemCreate):
    db_item = get_item(db, item_id)
    if db_item:
        for key, value in item.dict().items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    db_item = get_item(db, item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

# DynamicColumns CRUD 함수
def get_dynamic_column(db: Session, column_id: int):
    return db.query(models.DynamicColumns).filter(models.DynamicColumns.id == column_id).first()

def get_dynamic_columns(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DynamicColumns).offset(skip).limit(limit).all()

def create_dynamic_column(db: Session, column: schemas.DynamicColumnsCreate):
    db_column = models.DynamicColumns(**column.dict())
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    return db_column

def update_dynamic_column(db: Session, column_id: int, column: schemas.DynamicColumnsUpdate):
    db_column = get_dynamic_column(db, column_id)
    if db_column:
        update_data = column.dict(exclude_unset=True)
        
        # 데이터 필드가 있으면 기존 데이터와 병합
        if 'data' in update_data and update_data['data'] is not None:
            current_data = db_column.data or {}
            current_data.update(update_data['data'])
            update_data['data'] = current_data
            
        for key, value in update_data.items():
            setattr(db_column, key, value)
            
        db.commit()
        db.refresh(db_column)
    return db_column

def delete_dynamic_column(db: Session, column_id: int):
    db_column = get_dynamic_column(db, column_id)
    if db_column:
        db.delete(db_column)
        db.commit()
    return db_column

# DynamicSchema CRUD 함수
def get_dynamic_schema(db: Session, schema_id: int):
    return db.query(models.DynamicSchema).filter(models.DynamicSchema.id == schema_id).first()

def get_dynamic_schemas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DynamicSchema).offset(skip).limit(limit).all()

def create_dynamic_schema(db: Session, schema: schemas_dynamic.DynamicSchemaCreate):
    db_schema = models.DynamicSchema(
        name=schema.name,
        description=schema.description,
        schema_definition=schema.schema_definition.dict()
    )
    db.add(db_schema)
    db.commit()
    db.refresh(db_schema)
    return db_schema

# DynamicData CRUD 함수
def create_dynamic_data(db: Session, data_create: schemas_dynamic.DynamicDataCreate):
    # 스키마 가져오기
    schema = get_dynamic_schema(db, data_create.schema_id)
    if not schema:
        raise ValueError(f"Schema with id {data_create.schema_id} not found")
    
    # 스키마 정의 객체 생성
    schema_def = schemas_dynamic.SchemaDefinition(**schema.schema_definition)
    
    # 데이터 검증
    validated_data = schemas_dynamic.DynamicDataValidator.validate_data(
        schema_def, data_create.data
    )
    
    # 검증된 데이터로 DB 객체 생성
    db_data = models.DynamicData(
        schema_id=data_create.schema_id,
        data=validated_data
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

def get_dynamic_data(db: Session, data_id: int, include_deleted: bool = False):
    """
    동적 데이터 조회 (소프트 삭제된 항목 제외 옵션)
    """
    query = db.query(models.DynamicData).filter(models.DynamicData.id == data_id)
    
    if not include_deleted:
        # is_deleted 필드가 있는 경우에만 필터링
        if hasattr(models.DynamicData, 'is_deleted'):
            query = query.filter(models.DynamicData.is_deleted == False)
    
    return query.first()

def get_dynamic_data_by_schema(db: Session, schema_id: int, skip: int = 0, limit: int = 100, include_deleted: bool = False):
    """
    스키마 ID로 동적 데이터 조회 (소프트 삭제된 항목 제외 옵션)
    """
    query = db.query(models.DynamicData).filter(models.DynamicData.schema_id == schema_id)
    
    if not include_deleted:
        # is_deleted 필드가 있는 경우에만 필터링
        if hasattr(models.DynamicData, 'is_deleted'):
            query = query.filter(models.DynamicData.is_deleted == False)
    
    return query.offset(skip).limit(limit).all()

def soft_delete_dynamic_data(db: Session, data_id: int):
    """
    동적 데이터 소프트 삭제
    """
    db_data = get_dynamic_data(db, data_id, include_deleted=True)
    if db_data:
        # is_deleted 필드가 있는 경우에만 소프트 삭제
        if hasattr(models.DynamicData, 'is_deleted'):
            db_data.is_deleted = True
            db.commit()
            return db_data
        else:
            # is_deleted 필드가 없으면 하드 삭제
            db.delete(db_data)
            db.commit()
            return db_data
    return None

def restore_dynamic_data(db: Session, data_id: int):
    """
    소프트 삭제된 동적 데이터 복원
    """
    db_data = get_dynamic_data(db, data_id, include_deleted=True)
    if db_data and hasattr(models.DynamicData, 'is_deleted') and db_data.is_deleted:
        db_data.is_deleted = False
        db.commit()
        db.refresh(db_data)
    return db_data 