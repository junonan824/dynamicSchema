# 동적 JSON 스키마 API

동적 JSON 스키마를 정의하고 해당 스키마에 따라 데이터를 검증, 저장, 조회할 수 있는 API 서버입니다.

## 주요 기능

* **동적 스키마 관리**: JSON 스키마를 동적으로 정의하고 관리
* **데이터 검증**: 정의된 스키마에 따라 데이터 검증
* **데이터 저장 및 조회**: 검증된 데이터를 저장하고 다양한 조건으로 조회
* **필드 관리**: 스키마의 필드를 동적으로 추가, 수정, 삭제
* **예외 처리 및 로깅**: 모든 API 엔드포인트에 적절한 예외 처리와 로깅 구현

## 기술 스택

* **FastAPI**: 고성능 웹 프레임워크
* **SQLAlchemy**: ORM(Object-Relational Mapping)
* **Pydantic**: 데이터 검증 및 설정 관리
* **SQLite**: 데이터베이스
* **pytest**: 테스트 프레임워크

## 설치 방법

### 요구 사항

* Python 3.8 이상

### 설치 단계

1. 저장소 클론
   ```bash
   git clone https://github.com/yourusername/dynamic-json-schema-api.git
   cd dynamic-json-schema-api
   ```

2. 가상 환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 또는
   venv\Scripts\activate  # Windows
   ```

3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

## 실행 방법

### 개발 서버 실행

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 다음 URL에서 API에 접근할 수 있습니다:
- API 엔드포인트: http://localhost:8000
- API 문서(Swagger UI): http://localhost:8000/docs
- API 문서(ReDoc): http://localhost:8000/redoc

### 환경 변수 설정

`.env` 파일을 생성하여 다음과 같은 환경 변수를 설정할 수 있습니다:

```
DATABASE_URL=sqlite:///./app.db
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## API 사용 예시

### 1. 스키마 정의

```bash
curl -X POST "http://localhost:8000/dynamic-schemas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "사용자 프로필",
    "description": "사용자 정보를 저장하는 스키마",
    "schema_definition": {
      "name": "사용자 프로필",
      "description": "사용자 정보 스키마",
      "fields": {
        "이름": {
          "type": "string",
          "required": true,
          "description": "사용자 이름"
        },
        "나이": {
          "type": "integer",
          "required": true,
          "description": "사용자 나이"
        }
      }
    }
  }'
```

### 2. 스키마에 필드 추가

```bash
curl -X POST "http://localhost:8000/schema-fields/1/fields" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "이메일",
    "definition": {
      "type": "string",
      "required": false,
      "description": "사용자 이메일"
    }
  }'
```

### 3. 데이터 검증

```bash
curl -X POST "http://localhost:8000/dynamic-data/validate?schema_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "이름": "홍길동",
    "나이": 30,
    "이메일": "hong@example.com"
  }'
```

### 4. 데이터 저장

```bash
curl -X POST "http://localhost:8000/dynamic-data/" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_id": 1,
    "data": {
      "이름": "홍길동",
      "나이": 30,
      "이메일": "hong@example.com"
    }
  }'
```

### 5. 데이터 조회

```bash
curl -X GET "http://localhost:8000/dynamic-data/1"
```

## 테스트 실행

```bash
pytest
```

특정 테스트 파일 실행:

```bash
pytest tests/test_dynamic_schemas.py
```

## 프로젝트 구조

```
dynamic-json-schema-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 및 라우터 설정
│   ├── database.py          # 데이터베이스 연결 설정
│   ├── models.py            # SQLAlchemy 모델
│   ├── crud.py              # 데이터베이스 CRUD 작업
│   ├── schemas_dynamic.py   # Pydantic 모델 및 스키마
│   ├── middleware.py        # 미들웨어 (로깅 등)
│   ├── logger.py            # 로깅 설정
│   ├── static/              # 정적 파일
│   ├── utils/               # 유틸리티 함수
│   │   └── error_handlers.py # 오류 처리 유틸리티
│   └── routers/             # API 라우터
│       ├── dynamic_schemas.py
│       ├── dynamic_data.py
│       ├── dynamic_schema_fields.py
│       └── ...
├── tests/                   # 테스트 코드
│   ├── conftest.py
│   ├── test_dynamic_schemas.py
│   ├── test_dynamic_data.py
│   └── ...
├── logs/                    # 로그 파일 (자동 생성)
├── .env                     # 환경 변수 (예시 참조)
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.
