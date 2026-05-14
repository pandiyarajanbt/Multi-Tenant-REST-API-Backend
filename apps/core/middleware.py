import threading

_thread_local = threading.local()


def get_current_tenant():
    return getattr(_thread_local, "tenant", None)


class TenantMiddleware:
    """Resolves the tenant from the authenticated user and stores it thread-locally."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.tenant = None
        response = self.get_response(request)
        # Set after authentication middleware has run
        if hasattr(request, "user") and request.user.is_authenticated:
            _thread_local.tenant = getattr(request.user, "organization", None)
        return response
