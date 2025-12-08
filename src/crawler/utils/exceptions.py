"""
Custom exceptions for the TuoiTre crawler
"""


class CrawlerException(Exception):
    """Base exception for all crawler errors"""
    pass


class NetworkError(CrawlerException):
    """Raised when network-related errors occur"""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)


class ParseError(CrawlerException):
    """Raised when HTML/content parsing fails"""
    def __init__(self, message: str, url: str = None, element: str = None):
        self.url = url
        self.element = element
        super().__init__(message)


class MediaDownloadError(CrawlerException):
    """Raised when media download fails"""
    def __init__(self, message: str, media_url: str = None, media_type: str = None):
        self.media_url = media_url
        self.media_type = media_type
        super().__init__(message)


class ValidationError(CrawlerException):
    """Raised when data validation fails"""
    def __init__(self, message: str, field: str = None, value: any = None):
        self.field = field
        self.value = value
        super().__init__(message)


class RateLimitError(CrawlerException):
    """Raised when rate limiting is triggered"""
    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)
