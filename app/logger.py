import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 로그 디렉토리 생성
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 로거 설정
logger = logging.getLogger("dynamic_api")
logger.setLevel(logging.INFO)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# 파일 핸들러 (일반 로그)
file_handler = logging.FileHandler(log_dir / f"api_{datetime.now().strftime('%Y-%m-%d')}.log")
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# 파일 핸들러 (에러 로그)
error_handler = logging.FileHandler(log_dir / f"error_{datetime.now().strftime('%Y-%m-%d')}.log")
error_handler.setLevel(logging.ERROR)
error_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_format)

# 핸들러 추가
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_handler)

# JSON 로그 핸들러
class JsonFileHandler(logging.FileHandler):
    def __init__(self, filename):
        super().__init__(filename)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        if hasattr(record, 'path'):
            log_data['path'] = record.path
            
        if hasattr(record, 'method'):
            log_data['method'] = record.method
            
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
            
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
            
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
            
        if hasattr(record, 'exception'):
            log_data['exception'] = record.exception
        
        return json.dumps(log_data)

# JSON 로그 파일 핸들러 설정
json_handler = JsonFileHandler(log_dir / f"api_json_{datetime.now().strftime('%Y-%m-%d')}.log")
json_handler.setLevel(logging.INFO)
json_handler.setFormatter(JsonFormatter())
logger.addHandler(json_handler)

def get_logger():
    return logger

def log_request(request_id: str, method: str, path: str, client_ip: str, data: Dict[str, Any] = None):
    """API 요청 로깅"""
    extra = {
        'request_id': request_id,
        'method': method,
        'path': path,
        'client_ip': client_ip
    }
    
    log_msg = f"Request {request_id}: {method} {path}"
    if data:
        # 민감한 정보 필터링
        filtered_data = filter_sensitive_data(data)
        extra['request_data'] = filtered_data
        log_msg += f" - Data: {json.dumps(filtered_data)}"
    
    logger.info(log_msg, extra=extra)

def log_response(request_id: str, status_code: int, duration: float, data: Dict[str, Any] = None):
    """API 응답 로깅"""
    extra = {
        'request_id': request_id,
        'status_code': status_code,
        'duration': duration
    }
    
    log_msg = f"Response {request_id}: Status {status_code}, Duration {duration:.4f}s"
    if data:
        # 민감한 정보 필터링
        filtered_data = filter_sensitive_data(data)
        extra['response_data'] = filtered_data
        log_msg += f" - Data: {json.dumps(filtered_data)}"
    
    logger.info(log_msg, extra=extra)

def log_error(request_id: str, error: Exception, status_code: int = 500):
    """API 에러 로깅"""
    extra = {
        'request_id': request_id,
        'status_code': status_code,
        'exception': str(error)
    }
    
    logger.error(f"Error {request_id}: {str(error)}", exc_info=True, extra=extra)

def filter_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """민감한 정보 필터링"""
    if not data or not isinstance(data, dict):
        return data
    
    filtered = data.copy()
    sensitive_fields = ['password', 'token', 'secret', 'key', 'auth', 'credential']
    
    for key in data:
        for field in sensitive_fields:
            if field in key.lower():
                filtered[key] = "***FILTERED***"
                break
        
        # 중첩된 딕셔너리 처리
        if isinstance(data[key], dict):
            filtered[key] = filter_sensitive_data(data[key])
        
        # 리스트 내 딕셔너리 처리
        elif isinstance(data[key], list):
            filtered[key] = [
                filter_sensitive_data(item) if isinstance(item, dict) else item
                for item in data[key]
            ]
    
    return filtered 