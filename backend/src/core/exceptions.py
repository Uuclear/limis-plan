from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class LIMSException(HTTPException):
    def __init__(self, code: str, status_code: int = 400, detail: str = ""):
        super().__init__(status_code, {"code": code, "message": detail})

class AuthError(LIMSException):
    def __init__(self, msg: str, status: int = 401):
        super().__init__("AUTH_ERROR", status, msg)

class BusinessError(LIMSException):
    def __init__(self, msg: str, status: int = 400):
        super().__init__("BUSINESS_ERROR", status, msg)

class WorkflowError(LIMSException):
    def __init__(self, msg: str, status: int = 400):
        super().__init__("WORKFLOW_ERROR", status, msg)
