"""
Resilient HTTP Client for Task-Service
=======================================
Câu 8: Timeout + Retry + Circuit Breaker
- Timeout: 10 giây mặc định
- Retry: tối đa 3 lần, backoff 0.5s → 1s → 2s
- Circuit Breaker: ngắt 30s sau 3 lỗi liên tiếp
"""

import httpx
import asyncio
import time
from typing import Optional
from dataclasses import dataclass, field


# ==========================================
# CIRCUIT BREAKER
# ==========================================
@dataclass
class CircuitBreaker:
    """
    Circuit Breaker Pattern:
    - CLOSED: hoạt động bình thường
    - OPEN: ngắt kết nối, trả lỗi ngay (không gọi service)
    - HALF_OPEN: thử lại 1 request để kiểm tra service đã hồi phục chưa
    """
    failure_threshold: int = 3          # Số lỗi liên tiếp trước khi mở circuit
    recovery_timeout: float = 30.0      # Thời gian chờ trước khi thử lại (giây)
    failure_count: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: str = field(default="CLOSED", init=False)  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        """Ghi nhận request thành công → reset circuit"""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """Ghi nhận request thất bại → tăng failure count"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def can_execute(self) -> bool:
        """Kiểm tra có thể gửi request không"""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            # Kiểm tra đã qua thời gian recovery chưa
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN: cho phép 1 request thử
        return True


# Registry: mỗi service URL có 1 circuit breaker riêng
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Lấy hoặc tạo CircuitBreaker cho mỗi service"""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker()
    return _circuit_breakers[service_name]


# ==========================================
# RETRY VỚI EXPONENTIAL BACKOFF
# ==========================================
async def retry_request(
    method: str,
    url: str,
    service_name: str,
    max_retries: int = 3,
    timeout: float = 10.0,
    backoff_base: float = 0.5,
    **kwargs
) -> Optional[httpx.Response]:
    """
    Gửi HTTP request với:
    1. Timeout (mặc định 10s)
    2. Retry (tối đa 3 lần, exponential backoff)
    3. Circuit Breaker (ngắt 30s sau 3 lỗi liên tiếp)

    Trả về Response hoặc None nếu tất cả retry đều thất bại.
    """
    cb = get_circuit_breaker(service_name)

    if not cb.can_execute():
        return None  # Circuit đang OPEN, không gửi request

    last_error = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
                response = await client.request(method=method, url=url, **kwargs)

                if response.status_code < 500:
                    # Request thành công (kể cả 4xx là lỗi client, không phải lỗi service)
                    cb.record_success()
                    return response
                else:
                    # 5xx → server error, cần retry
                    cb.record_failure()
                    last_error = f"HTTP {response.status_code}"

        except httpx.TimeoutException:
            cb.record_failure()
            last_error = "Timeout"
        except httpx.ConnectError:
            cb.record_failure()
            last_error = "Connection refused"
        except Exception as e:
            cb.record_failure()
            last_error = str(e)

        # Exponential backoff trước khi retry
        if attempt < max_retries - 1:
            wait_time = backoff_base * (2 ** attempt)  # 0.5s, 1s, 2s
            await asyncio.sleep(wait_time)

    return None


# ==========================================
# HELPER FUNCTIONS
# ==========================================
async def resilient_get(url: str, service_name: str, timeout: float = 10.0, **kwargs) -> Optional[httpx.Response]:
    """GET request với retry + circuit breaker"""
    return await retry_request("GET", url, service_name, timeout=timeout, **kwargs)


async def resilient_post(url: str, service_name: str, timeout: float = 10.0, **kwargs) -> Optional[httpx.Response]:
    """POST request với retry + circuit breaker"""
    return await retry_request("POST", url, service_name, timeout=timeout, **kwargs)


async def resilient_put(url: str, service_name: str, timeout: float = 10.0, **kwargs) -> Optional[httpx.Response]:
    """PUT request với retry + circuit breaker"""
    return await retry_request("PUT", url, service_name, timeout=timeout, **kwargs)


async def resilient_delete(url: str, service_name: str, timeout: float = 10.0, **kwargs) -> Optional[httpx.Response]:
    """DELETE request với retry + circuit breaker"""
    return await retry_request("DELETE", url, service_name, timeout=timeout, **kwargs)


def get_friendly_error(service_name: str) -> str:
    """Trả thông báo lỗi thân thiện cho người dùng khi service không phản hồi"""
    cb = get_circuit_breaker(service_name)
    if cb.state == "OPEN":
        return f"Dịch vụ {service_name} tạm thời không khả dụng. Vui lòng thử lại sau 30 giây."
    return f"Dịch vụ {service_name} không phản hồi sau nhiều lần thử. Vui lòng thử lại sau."
