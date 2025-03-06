import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logger import log_request, log_response, log_error

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 클라이언트 IP 주소 가져오기
        client_ip = request.client.host if request.client else "unknown"
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 본문 로깅 (JSON인 경우)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.json()
            except Exception:
                # JSON이 아닌 경우 무시
                pass
        
        # 요청 로깅
        log_request(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            data=request_body
        )
        
        # 응답 헤더에 요청 ID 추가
        response = Response()
        try:
            # 다음 미들웨어 또는 엔드포인트 호출
            response = await call_next(request)
            
            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id
            
            # 처리 시간 계산
            duration = time.time() - start_time
            
            # 응답 로깅
            log_response(
                request_id=request_id,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
        except Exception as e:
            # 예외 발생 시 로깅
            duration = time.time() - start_time
            log_error(request_id=request_id, error=e)
            
            # 500 에러 응답
            return Response(
                content={"detail": "Internal Server Error"},
                status_code=500,
                headers={"X-Request-ID": request_id}
            ) 