from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import os

from .database import engine
from . import models
from .routers import items, dynamic_columns, dynamic_schemas, dynamic_data, dynamic_schema_fields
from .middleware import LoggingMiddleware
from .utils.error_handlers import APIError, handle_validation_error, handle_api_error, handle_generic_error
from .logger import get_logger, log_error

# 로거 가져오기
logger = get_logger()

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# 정적 파일 디렉토리 생성
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

app = FastAPI(
    title="동적 JSON 스키마 API",
    description="""
    동적 JSON 스키마를 정의하고 해당 스키마에 따라 데이터를 검증, 저장, 조회할 수 있는 API입니다.
    
    ## 주요 기능
    
    * **동적 스키마 관리**: JSON 스키마를 동적으로 정의하고 관리
    * **데이터 검증**: 정의된 스키마에 따라 데이터 검증
    * **데이터 저장 및 조회**: 검증된 데이터를 저장하고 다양한 조건으로 조회
    * **필드 관리**: 스키마의 필드를 동적으로 추가, 수정, 삭제
    
    ## 사용 예시
    
    1. 스키마 정의
    2. 스키마에 필드 추가
    3. 데이터 검증
    4. 데이터 저장
    5. 데이터 조회 및 검색
    """,
    version="1.0.0",
    docs_url=None,  # 기본 /docs 엔드포인트 비활성화
    redoc_url=None  # 기본 /redoc 엔드포인트 비활성화
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 실제 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# 커스텀 OpenAPI 스키마 생성
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 태그 정보 추가
    openapi_schema["tags"] = [
        {
            "name": "dynamic-schemas",
            "description": "동적 JSON 스키마 관리 API",
        },
        {
            "name": "schema-fields",
            "description": "스키마 필드 관리 API",
        },
        {
            "name": "dynamic-data",
            "description": "동적 데이터 관리 API",
        },
        {
            "name": "items",
            "description": "기본 아이템 관리 API",
        },
        {
            "name": "dynamic-columns",
            "description": "동적 컬럼 관리 API",
        },
    ]
    
    # 서버 정보 추가
    openapi_schema["servers"] = [
        {
            "url": "/",
            "description": "현재 서버"
        }
    ]
    
    # 보안 스키마 추가 (필요한 경우)
    # openapi_schema["components"]["securitySchemes"] = {
    #     "bearerAuth": {
    #         "type": "http",
    #         "scheme": "bearer",
    #         "bearerFormat": "JWT",
    #     }
    # }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 커스텀 Swagger UI 엔드포인트
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png"
    )

# 커스텀 ReDoc 엔드포인트
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.png"
    )

# 예외 핸들러 등록
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 처리"""
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # 오류 로깅
    log_error(request_id=request_id, error=exc, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # 응답 생성
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=handle_validation_error(exc)
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic 검증 오류 처리"""
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # 오류 로깅
    log_error(request_id=request_id, error=exc, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    # 응답 생성
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=handle_validation_error(exc)
    )

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """API 오류 처리"""
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # 오류 로깅
    log_error(request_id=request_id, error=exc, status_code=exc.status_code)
    
    # 응답 생성
    return JSONResponse(
        status_code=exc.status_code,
        content=handle_api_error(exc)
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    # 요청 ID 가져오기
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # 오류 로깅
    log_error(request_id=request_id, error=exc)
    
    # 응답 생성
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=handle_generic_error(exc)
    )

# 라우터 포함
app.include_router(items.router)
app.include_router(dynamic_columns.router)
app.include_router(dynamic_schemas.router)
app.include_router(dynamic_data.router)
app.include_router(dynamic_schema_fields.router)

@app.get("/", tags=["root"])
def read_root():
    """API 루트 엔드포인트"""
    logger.info("Root endpoint called")
    return {
        "message": "동적 JSON 스키마 API에 오신 것을 환영합니다!",
        "documentation": "/docs",
        "version": app.version
    }

@app.get("/health", tags=["system"])
def health_check():
    """서버 상태 확인 엔드포인트"""
    return {"status": "healthy", "version": app.version} 