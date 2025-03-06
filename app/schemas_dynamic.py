from pydantic import BaseModel, create_model, validator, ValidationError, Field
from typing import Dict, Any, Optional, List, Union, Type, get_type_hints
from datetime import datetime
import json

# 기본 스키마 정의 모델
class SchemaDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    fields: Dict[str, Dict[str, Any]]
    
    @validator('fields')
    def validate_field_definitions(cls, fields):
        valid_types = ['string', 'number', 'integer', 'boolean', 'array', 'object', 'date', 'datetime']
        
        for field_name, field_def in fields.items():
            if 'type' not in field_def:
                raise ValueError(f"Field '{field_name}' must have a 'type' property")
            
            field_type = field_def['type']
            if field_type not in valid_types:
                raise ValueError(f"Field '{field_name}' has invalid type '{field_type}'. Must be one of {valid_types}")
                
            # 배열 타입인 경우 items 속성 필요
            if field_type == 'array' and 'items' not in field_def:
                raise ValueError(f"Array field '{field_name}' must have an 'items' property")
                
            # 객체 타입인 경우 properties 속성 필요
            if field_type == 'object' and 'properties' not in field_def:
                raise ValueError(f"Object field '{field_name}' must have a 'properties' property")
        
        return fields

# 동적 스키마 저장 모델
class DynamicSchemaBase(BaseModel):
    name: str
    description: Optional[str] = None
    schema_definition: SchemaDefinition

class DynamicSchemaCreate(DynamicSchemaBase):
    pass

class DynamicSchema(DynamicSchemaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# 동적 데이터 검증 클래스
class DynamicDataValidator:
    @staticmethod
    def get_pydantic_type(field_type: str) -> Type:
        type_mapping = {
            'string': str,
            'number': float,
            'integer': int,
            'boolean': bool,
            'date': datetime.date,
            'datetime': datetime,
            'array': List,
            'object': Dict[str, Any]
        }
        return type_mapping.get(field_type, Any)
    
    @staticmethod
    def create_model_from_schema(schema_def: SchemaDefinition) -> Type[BaseModel]:
        """스키마 정의로부터 Pydantic 모델 생성"""
        field_definitions = {}
        
        for field_name, field_def in schema_def.fields.items():
            field_type = field_def['type']
            is_required = field_def.get('required', False)
            description = field_def.get('description', '')
            default = field_def.get('default', ... if is_required else None)
            
            # 기본 타입 처리
            if field_type in ['string', 'number', 'integer', 'boolean', 'date', 'datetime']:
                pydantic_type = DynamicDataValidator.get_pydantic_type(field_type)
                field_definitions[field_name] = (
                    Optional[pydantic_type] if not is_required else pydantic_type, 
                    Field(default=default, description=description)
                )
            
            # 배열 타입 처리
            elif field_type == 'array':
                items_type = field_def['items'].get('type', 'string')
                pydantic_type = List[DynamicDataValidator.get_pydantic_type(items_type)]
                field_definitions[field_name] = (
                    Optional[pydantic_type] if not is_required else pydantic_type,
                    Field(default=default, description=description)
                )
            
            # 객체 타입 처리
            elif field_type == 'object':
                field_definitions[field_name] = (
                    Optional[Dict[str, Any]] if not is_required else Dict[str, Any],
                    Field(default=default, description=description)
                )
        
        # 동적 모델 생성
        return create_model(
            f"Dynamic{schema_def.name.replace(' ', '')}Model",
            **field_definitions
        )
    
    @staticmethod
    def validate_data(schema_def: SchemaDefinition, data: Dict[str, Any]) -> Dict[str, Any]:
        """스키마 정의에 따라 데이터 검증"""
        model_class = DynamicDataValidator.create_model_from_schema(schema_def)
        try:
            validated_data = model_class(**data)
            return validated_data.dict()
        except ValidationError as e:
            raise ValueError(f"Data validation failed: {str(e)}")

# 동적 데이터 모델
class DynamicDataBase(BaseModel):
    schema_id: int
    data: Dict[str, Any]

class DynamicDataCreate(DynamicDataBase):
    pass

class DynamicData(DynamicDataBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True 