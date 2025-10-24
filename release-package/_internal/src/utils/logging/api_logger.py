class ApiLogger:
    """Logs específicos para operaciones de API"""
    
    def __init__(self, base_logger):
        self.base_logger = base_logger
    
    def log_api_call(self, endpoint: str, method: str, status_code: int = None, response_time: float = None):
        """Log específico para llamadas API"""
        message = f"API {method} {endpoint}"
        if status_code:
            message += f" - Status: {status_code}"
        if response_time:
            message += f" - Time: {response_time:.2f}s"
        
        self.base_logger.log_info(message)
    
    def log_api_error(self, endpoint: str, method: str, error: str, status_code: int = None):
        """Log específico para errores de API"""
        message = f"API_ERROR {method} {endpoint}"
        if status_code:
            message += f" - Status: {status_code}"
        message += f" - Error: {error}"
        
        self.base_logger.log_error(message)
    
    def log_rate_limit(self, endpoint: str, retry_after: int = None):
        """Log para rate limiting"""
        message = f"API_RATE_LIMIT {endpoint}"
        if retry_after:
            message += f" - Retry after: {retry_after}s"
        
        self.base_logger.log_warning(message)