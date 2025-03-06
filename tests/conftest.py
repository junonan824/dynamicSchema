import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, get_db
from app.main import app

# 테스트용 인메모리 SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # 테스트 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 테스트 세션 생성
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    # 테스트 후 테이블 삭제
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # 테스트용 의존성 오버라이드
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # 테스트 클라이언트 생성
    with TestClient(app) as client:
        yield client
    
    # 테스트 후 의존성 오버라이드 제거
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_schema(client):
    """테스트용 스키마 생성"""
    schema_data = {
        "name": "테스트 스키마",
        "description": "테스트용 스키마입니다",
        "schema_definition": {
            "name": "테스트 스키마",
            "description": "테스트용 스키마입니다",
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
    
    response = client.post("/dynamic-schemas/", json=schema_data)
    assert response.status_code == 200
    return response.json() 