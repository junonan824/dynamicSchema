import pytest

def test_add_field(client, test_schema):
    """필드 추가 테스트"""
    schema_id = test_schema["id"]
    
    field_definition = {
        "name": "주소",
        "definition": {
            "type": "string",
            "required": False,
            "description": "사용자 주소"
        }
    }
    
    response = client.post(f"/schema-fields/{schema_id}/fields", json=field_definition)
    assert response.status_code == 200
    result = response.json()
    assert "주소" in result["schema_definition"]["fields"]
    assert result["schema_definition"]["fields"]["주소"]["type"] == "string"

def test_update_field(client, test_schema):
    """필드 업데이트 테스트"""
    schema_id = test_schema["id"]
    field_name = "이메일"  # 기존 필드
    
    updated_definition = {
        "type": "string",
        "required": True,  # 필수 필드로 변경
        "description": "사용자 이메일 (필수)",
        "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"  # 이메일 패턴 추가
    }
    
    response = client.put(f"/schema-fields/{schema_id}/fields/{field_name}", json=updated_definition)
    assert response.status_code == 200
    result = response.json()
    assert field_name in result["schema_definition"]["fields"]
    assert result["schema_definition"]["fields"][field_name]["required"] == True
    assert "pattern" in result["schema_definition"]["fields"][field_name]

def test_delete_field(client, test_schema):
    """필드 삭제 테스트"""
    schema_id = test_schema["id"]
    
    # 먼저 새 필드 추가
    field_definition = {
        "name": "임시필드",
        "definition": {
            "type": "string",
            "required": False
        }
    }
    
    client.post(f"/schema-fields/{schema_id}/fields", json=field_definition)
    
    # 필드 삭제
    response = client.delete(f"/schema-fields/{schema_id}/fields/임시필드")
    assert response.status_code == 200
    result = response.json()
    assert "임시필드" not in result["schema_definition"]["fields"]

def test_get_fields(client, test_schema):
    """필드 목록 조회 테스트"""
    schema_id = test_schema["id"]
    
    response = client.get(f"/schema-fields/{schema_id}/fields")
    assert response.status_code == 200
    result = response.json()
    assert "fields" in result
    assert "이름" in result["fields"]
    assert "나이" in result["fields"]
    assert "이메일" in result["fields"]

def test_bulk_add_fields(client, test_schema):
    """여러 필드 한 번에 추가 테스트"""
    schema_id = test_schema["id"]
    
    fields = [
        {
            "name": "전화번호",
            "definition": {
                "type": "string",
                "required": False,
                "description": "사용자 전화번호"
            }
        },
        {
            "name": "주소",
            "definition": {
                "type": "string",
                "required": False,
                "description": "사용자 주소"
            }
        }
    ]
    
    response = client.post(f"/schema-fields/{schema_id}/bulk-add-fields", json=fields)
    assert response.status_code == 200
    result = response.json()
    assert "전화번호" in result["schema_definition"]["fields"]
    assert "주소" in result["schema_definition"]["fields"] 