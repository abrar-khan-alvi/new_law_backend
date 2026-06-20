from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable. Please try again later.'
    default_code = 'service_unavailable'


class QuotaExceeded(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Usage quota exceeded for your current plan.'
    default_code = 'quota_exceeded'


def custom_exception_handler(exc, context):
    """
    Wrap DRF's handler to return a consistent error envelope:
        {"error": {"detail": ..., "code": ...}}
    """
    response = drf_exception_handler(exc, context)
    if response is not None:
        detail = response.data
        code = getattr(exc, 'default_code', None)
        if isinstance(detail, dict) and 'detail' in detail:
            response.data = {'error': {'detail': detail['detail'], 'code': code}}
        else:
            response.data = {'error': {'detail': detail, 'code': code}}
    return response
