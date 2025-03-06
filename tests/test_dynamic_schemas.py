import pytest

def test_create_schema(client):
    """스키마 생성 테스트"""
    schema_data = {
        "name": "사용자 정보",
        "description": "사용자 정보를 저장하는 스키마",
        "schema_definition": {
            "name": "사용자 정보",
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
                }
            }
        }
    }
    
    response = client.post("/dynamic-schemas/", json=schema_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == schema_data["name"]
    assert data["description"] == schema_data["description"]
    assert "id" in data
    assert "created_at" in data

def test_get_schema(client, test_schema):
    """스키마 조회 테스트"""
    schema_id = test_schema["id"]
    
    response = client.get(f"/dynamic-schemas/{schema_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == schema_id
    assert data["name"] == test_schema["name"]

def test_get_schemas(client, test_schema):
    """스키마 목록 조회 테스트"""
    response = client.get("/dynamic-schemas/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # 생성한 테스트 스키마가 목록에 있는지 확인
    schema_ids = [schema["id"] for schema in data]
    assert test_schema["id"] in schema_ids

def test_invalid_schema(client):
    """유효하지 않은 스키마 생성 테스트"""
    # 필수 필드 누락
    invalid_schema = {
        "name": "잘못된 스키마",
        "schema_definition": {
            "name": "잘못된 스키마",
            "fields": {
                "이름": {
                    "type": "invalid_type",  # 유효하지 않은 타입
                    "required": True
                }
            }
        }
    }
    
    response = client.post("/dynamic-schemas/", json=invalid_schema)
    assert response.status_code == 422  # Unprocessable Entity 