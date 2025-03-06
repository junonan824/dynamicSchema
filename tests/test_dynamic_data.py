import pytest

def test_create_data(client, test_schema):
    """데이터 생성 테스트"""
    schema_id = test_schema["id"]
    
    data = {
        "schema_id": schema_id,
        "data": {
            "이름": "홍길동",
            "나이": 30,
            "이메일": "hong@example.com"
        }
    }
    
    response = client.post("/dynamic-data/", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["schema_id"] == schema_id
    assert result["data"]["이름"] == "홍길동"
    assert result["data"]["나이"] == 30
    assert "id" in result
    assert "created_at" in result

def test_validate_data(client, test_schema):
    """데이터 검증 테스트"""
    schema_id = test_schema["id"]
    
    # 유효한 데이터
    valid_data = {
        "이름": "홍길동",
        "나이": 30,
        "이메일": "hong@example.com"
    }
    
    response = client.post(f"/dynamic-data/validate?schema_id={schema_id}", json=valid_data)
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] == True
    assert "validated_data" in result
    
    # 유효하지 않은 데이터 (필수 필드 누락)
    invalid_data = {
        "이메일": "hong@example.com"
    }
    
    response = client.post(f"/dynamic-data/validate?schema_id={schema_id}", json=invalid_data)
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] == False
    assert "error" in result

def test_get_data(client, test_schema):
    """데이터 조회 테스트"""
    schema_id = test_schema["id"]
    
    # 데이터 생성
    data = {
        "schema_id": schema_id,
        "data": {
            "이름": "홍길동",
            "나이": 30,
            "이메일": "hong@example.com"
        }
    }
    
    create_response = client.post("/dynamic-data/", json=data)
    assert create_response.status_code == 200
    created_data = create_response.json()
    data_id = created_data["id"]
    
    # ID로 데이터 조회
    response = client.get(f"/dynamic-data/{data_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == data_id
    assert result["schema_id"] == schema_id
    assert result["data"]["이름"] == "홍길동"
    
    # 스키마 ID로 데이터 조회
    response = client.get(f"/dynamic-data/?schema_id={schema_id}")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    
    # 생성한 데이터가 목록에 있는지 확인
    data_ids = [item["id"] for item in results]
    assert data_id in data_ids

def test_update_data(client, test_schema):
    """데이터 업데이트 테스트"""
    schema_id = test_schema["id"]
    
    # 데이터 생성
    data = {
        "schema_id": schema_id,
        "data": {
            "이름": "홍길동",
            "나이": 30,
            "이메일": "hong@example.com"
        }
    }
    
    create_response = client.post("/dynamic-data/", json=data)
    assert create_response.status_code == 200
    created_data = create_response.json()
    data_id = created_data["id"]
    
    # 데이터 업데이트
    update_data = {
        "이름": "김철수",
        "나이": 25,
        "이메일": "kim@example.com"
    }
    
    response = client.put(f"/dynamic-data/{data_id}", json=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == data_id
    assert result["data"]["이름"] == "김철수"
    assert result["data"]["나이"] == 25
    assert result["data"]["이메일"] == "kim@example.com"
    
    # 부분 업데이트
    patch_data = {
        "나이": 26
    }
    
    response = client.patch(f"/dynamic-data/{data_id}/partial", json=patch_data)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == data_id
    assert result["data"]["이름"] == "김철수"  # 기존 값 유지
    assert result["data"]["나이"] == 26  # 업데이트된 값
    assert result["data"]["이메일"] == "kim@example.com"  # 기존 값 유지

def test_delete_data(client, test_schema):
    """데이터 삭제 테스트"""
    schema_id = test_schema["id"]
    
    # 데이터 생성
    data = {
        "schema_id": schema_id,
        "data": {
            "이름": "홍길동",
            "나이": 30,
            "이메일": "hong@example.com"
        }
    }
    
    create_response = client.post("/dynamic-data/", json=data)
    assert create_response.status_code == 200
    created_data = create_response.json()
    data_id = created_data["id"]
    
    # 데이터 삭제
    response = client.delete(f"/dynamic-data/{data_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    
    # 삭제된 데이터 조회 시도
    response = client.get(f"/dynamic-data/{data_id}")
    assert response.status_code == 404

def test_search_data(client, test_schema):
    """데이터 검색 테스트"""
    schema_id = test_schema["id"]
    
    # 데이터 여러 개 생성
    data1 = {
        "schema_id": schema_id,
        "data": {
            "이름": "홍길동",
            "나이": 30,
            "이메일": "hong@example.com"
        }
    }
    
    data2 = {
        "schema_id": schema_id,
        "data": {
            "이름": "김철수",
            "나이": 25,
            "이메일": "kim@example.com"
        }
    }
    
    client.post("/dynamic-data/", json=data1)
    client.post("/dynamic-data/", json=data2)
    
    # 이름으로 검색
    search_criteria = {
        "field_path": "이름",
        "operator": "eq",
        "value": "홍길동"
    }
    
    response = client.post("/dynamic-data/search", json=search_criteria)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    assert all(item["data"]["이름"] == "홍길동" for item in results)
    
    # 나이 범위로 검색
    search_criteria = {
        "and": [
            {"field_path": "나이", "operator": "gte", "value": 25},
            {"field_path": "나이", "operator": "lte", "value": 30}
        ]
    }
    
    response = client.post("/dynamic-data/search", json=search_criteria)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= 2
    assert all(25 <= item["data"]["나이"] <= 30 for item in results) 