import json
from enum import Enum
from typing import Generic, Optional, TypeVar

T = TypeVar('T')

class Result(Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"

    def __str__(self):
        # __str__을 오버라이드하여 Enum의 값을 그대로 반환하도록 함
        return self.value

class CommonResponse(Generic[T]):
    def __init__(self, result: Result, errorCode: str, message: str, data: Optional[T]):
        self.result = result
        self.errorCode = errorCode
        self.message = message
        self.data = data

    @classmethod
    def success(cls, data: T, message: str = "") -> 'CommonResponse[T]':
        """성공 응답 생성"""
        return cls(Result.SUCCESS, "", message, data)

    @classmethod
    def fail(cls, errorCode: str, message: str, data: Optional[T] = None) -> 'CommonResponse[T]':
        """실패 응답 생성 (에러코드, 메시지, 선택적 데이터 포함)"""
        return cls(Result.FAIL, errorCode, message, data)

    @classmethod
    def fail_with_error(cls, error_code_obj: 'ErrorCode') -> 'CommonResponse[T]':
        """ErrorCode 객체를 받아 실패 응답 생성"""
        return cls(Result.FAIL, error_code_obj.name(), error_code_obj.get_error_msg(), None)

    def to_dict(self):
        """JSON 직렬화 가능한 dict로 변환"""
        return {
            "result": self.result.value,
            "errorCode": self.errorCode,
            "message": self.message,
            "data": self.data
        }

    def __str__(self):
        return (f"result={self.result}, errorCode='{self.errorCode}', "
                f"message='{self.message}', data={self.data}")

# 에러 코드를 표현하기 위한 예제 클래스
class ErrorCode:
    def __init__(self, name: str, error_msg: str):
        self._name = name
        self._error_msg = error_msg

    def name(self) -> str:
        return self._name

    def get_error_msg(self) -> str:
        return self._error_msg

# --- 샘플 처리 코드 ---

if __name__ == "__main__":
    # 성공 응답 예제
    data_success = {"master": "Alice", "id": 123}
    response_success = CommonResponse.success(data_success, "Operation completed successfully.")
    print("Success Response:")
    print(response_success)
    print()

    # 실패 응답 예제 (에러 코드와 메시지만)
    response_fail = CommonResponse.fail("404", "Resource not found")
    print("Fail Response:")
    print(response_fail)
    print()

    # 실패 응답 예제 (에러 코드, 메시지와 데이터 포함)
    response_fail_with_data = CommonResponse.fail("400", "Bad Request", data={"field": "username"})
    print("Fail Response with Data:")
    print(response_fail_with_data)
    print()

    # ErrorCode 객체를 사용한 실패 응답 예제
    error_code_obj = ErrorCode("500", "Internal server error")
    response_fail_error_code = CommonResponse.fail_with_error(error_code_obj)
    print("Fail Response using ErrorCode object:")
    print(response_fail_error_code)
